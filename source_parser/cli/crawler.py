# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# pylint: disable=too-many-instance-attributes,no-member
"""
CrawlCrawler crawls crawled github repos and applies
observers to clone, walk and parser source code
files in a scalable parallel fashion.
"""

import json
import logging
from itertools import cycle
from contextlib import ExitStack
from pathlib import Path
from tqdm import tqdm
import psutil
import ray

from source_parser import OPEN_PROTOCOLS, __version__

LOGGER = logging.getLogger(__name__)


def fmt_num(integer):
    """make numbers readable e.g. 1000 -> '1_000'"""
    integer = str(integer)
    dec = len(integer)
    groups = [integer[: dec % 3]] if dec % 3 else []
    groups.extend([integer[i: i + 3] for i in range(dec % 3, dec, 3)])
    return ",".join(groups)


def report(msg_kwargs, print_stdout=False, fmt=fmt_num):
    """ report statistics of processing run """
    msg = []
    for label, contents in msg_kwargs.items():
        msg.append(f"{label}:")
        maxw = max(map(len, contents.keys())) + 2
        for k, v in contents.items():
            lab = f"{k}:".ljust(maxw)
            msg.append(f"    {lab}{fmt(v)}")
    LOGGER.report("\n".join(msg))
    if print_stdout:
        tqdm.write("\n".join(msg))


@ray.remote
def notify(observers, task, timeout=20):
    """
    Notify the observers

    Parameters
    ----------
    observers : list[Observer]
        list of observers objects
    task: dict
        must have key 'url' for repository url
    timeout: int
        number of seconds to allow for git cloning

    Returns
    -------
    output : dict, dict
        output, statistics
            output[observer] = results
            output['statistics'] = stats dict accumulated
            (for when errors occur)
    """
    statistics = {}
    for obs in observers:
        for label in obs.statistic_labels:
            statistics[label] = 0

    output = {"statistics": statistics, "error_msgs": []}
    for obs_i, obs in enumerate(observers):
        try:
            # parser must be instantiated here as it is not pickleable
            output[obs_i], error_msgs = obs.notify(
                statistics, task, timeout=timeout
            )
            output["error_msgs"].extend(error_msgs)
        except (KeyboardInterrupt, SystemExit):
            LOGGER.info("Quitting...")
            raise
        except Exception as err:
            output["error_msgs"].append(
                f"Processing url {task['url']} yielded {err}")

    return output


@ray.remote
class Deduplicate:
    skip = ("statistics", "error_msgs")

    def __init__(self):
        self.seenfiles = {}
        self.duplicates = {}

    def process(self, output):
        for obs_i, results in output.items():
            if obs_i not in self.skip:
                unique_results = []
                for result in results:

                    # copy to prevent memory pinning
                    file_hash = str(result["file_hash"])
                    if file_hash in self.seenfiles:
                        self.seenfiles[file_hash] += 1
                        output["statistics"]["duplicate_items"] += 1
                    else:
                        self.seenfiles[file_hash] = 1
                        # save url and path to first copy of duplicate
                        self.duplicates[file_hash] = {
                            k: str(result[k]) for k in ("url", "relative_path")
                        }
                        unique_results.append(result)

                output[obs_i] = unique_results
        return output

    def report_duplicates(self):
        result = {}
        for file_hash, count in self.seenfiles.items():
            if file_hash in self.duplicates:
                res = {"count": count}
                res.update(self.duplicates[file_hash])
                result[file_hash] = res
        return result


@ray.remote
class ProcessResults:

    def __init__(self, observers, num_tasks, protocol, part=None):
        self.seenfiles = {}
        self.statistics = {}  # statistics[label] = value
        self.statistics["number_of_tasks"] = num_tasks
        self.statistics["tasks_finished"] = 0
        self.statistics["items_written"] = 0
        self.statistics["bytes_written"] = 0
        for obs in observers:
            for label in obs.statistic_labels:
                self.statistics[label] = 0

        open_protocol = OPEN_PROTOCOLS[protocol]
        self.stack = ExitStack()
        self.savestreams = {
            obs_i: self.stack.enter_context(
                open_protocol(self.add_part_to_name(obs.savefile, part), "wb")
            )
            for obs_i, obs in enumerate(observers)
        }

    @staticmethod
    def add_part_to_name(name, part):
        if not part:
            return name
        dotsplit = name.split(".")
        dotsplit[0] += f"-part-{part}"
        return ".".join(dotsplit)

    def process(self, output):
        # pull out errors and accumulate statistics
        msg = str(output.pop("error_msgs")) if "error_msgs" in output else []
        for lab, s in output.pop("statistics").items():
            self.statistics[lab] += s

        for obs_i, results in output.items():
            for result in results:

                n_bytes = self.savestreams[obs_i].write(
                    (json.dumps(result) + "\n").encode("utf-8")
                )
                self.statistics["items_written"] += 1
                self.statistics["bytes_written"] += n_bytes

        self.statistics["tasks_finished"] += 1
        return self.statistics, msg

    def report_stats(self):
        return self.statistics

    def close(self):
        self.stack.close()


class PipelineDispatch:
    def __init__(self, observers, tasks, message, **kwargs):
        if "compression" in kwargs:
            assert kwargs["compression"] in OPEN_PROTOCOLS
        self.num_dedupe = kwargs.get("num_dedupe_procs", 1)
        num_save_files = kwargs.get("num_save_files", 1)

        self.tasks = list(tasks)  # copy to prevent side effects
        self.notify = message
        self.processor_pool = []

        self.obs_id = ray.put(observers)

        self.dedupe_pool = [
            Deduplicate.remote()
            for _ in range(self.num_dedupe + 1 if self.num_dedupe > 1 else 1)
        ]
        self.dedupe_cyle = cycle(
            self.dedupe_pool[1:] if self.num_dedupe > 1 else self.dedupe_pool
        )

        processor_args = (self.obs_id, len(tasks),
                          kwargs.get("compression", "lz4"))
        if num_save_files > 1:
            self.processor_pool = [
                ProcessResults.remote(*processor_args, part=i)
                for i in range(num_save_files)
            ]
        else:
            self.processor_pool = [ProcessResults.remote(*processor_args)]
        self.processor_cycle = cycle(self.processor_pool)

        self.result_id_queue = []

    def push(self):
        if self.tasks:
            self.result_id_queue.append(
                self.notify.remote(self.obs_id, self.tasks.pop(0))
            )

    def pop(self):
        if self.result_id_queue:
            ready, self.result_id_queue = ray.wait(self.result_id_queue)
            return ready
        return []

    def warmup(self, num_workers):
        for _ in range(num_workers if num_workers > 0 else len(self.tasks)):
            self.push()

    def __iter__(self):
        for deduper, processor in zip(self.dedupe_cyle, self.processor_cycle):
            ready = self.pop()  # process the next one that's ready
            self.push()  # replace consumed task

            if ready:
                res_id = deduper.process.remote(ready[0])
                if self.num_dedupe > 1:
                    res_id = self.dedupe_pool[0].process.remote(res_id)
                yield processor.process.remote(res_id)
            else:
                break

    def close(self):
        for processor in self.processor_pool:
            processor.close.remote()

    def report_duplicates(self):
        reports = [
            ray.get(deduper.report_duplicates.remote())
            for deduper in self.dedupe_pool
        ]
        result = reports[0]
        for rep in reports[1:]:
            for k, v in rep.items():
                if k in result:
                    result[k]['count'] += v['count']
                else:
                    result[k] = v
                result.update(rep)
        return result

    def report_stats(self):
        reports = [
            ray.get(processor.report_stats.remote())
            for processor in self.processor_pool
        ]
        result = reports[0]
        for rep in reports[1:]:
            for lab, stat in rep.items():
                result[lab] += stat
        return result

    def save_dupe_report(self, processed_dir, **kwargs):
        if "duplicate_report_file" in kwargs:
            time = kwargs["duplicate_report_file"]
            dupe_report_file = Path(processed_dir)
            dupe_report_file /= f'{time}_duplicate_report_file.json'
            with open(dupe_report_file, "w", encoding='utf-8') as fout:
                json.dump(self.report_duplicates(), fout)


class CrawlCrawler:
    """
    Crawls Crawled Data, provides subjects for the observers to process.
    """

    def __init__(self, observers, processed_dir):
        """
        Initialize the CrawlCrawler

        Parameters
        ----------
        observers : list
            list of Observer objects
        processed_dir : str
            path to directory where results should be stored
        """

        self.observers = observers
        self.processed_dir = processed_dir

        if not isinstance(observers, list):
            raise TypeError("observers must be type list")

    def speak(self):
        """ Have all the observers speak """
        for obs in self.observers:
            obs.speak()

    def map(self, tasks, num_cpus=None, num_workers=None, **kwargs):
        """
        Walk `crawldirs` and for each file, notify the observers, saving results in
        files specified by the observers.

        Parameters
        ----------
        tasks: List[Dict[str, str]]
            list of tasks, requiring at least a 'url' key containing
            a git repo URL, and optionally a 'license' key if known.
        num_cops: int (optional)
            the number of CPUs to allow usage, defaults to the number of
            available CPUs - 1.
        num_workers: int (optional)
            the number of tasks to dispatch at a time, defaults to twice
            the CPU count. Larger numbers for tasks which differ a lot
            in their time improves performance.
        (kwargs)
        report_freq : int (optional)
            frequency with which to report statistics
            (defaults to every 5000 files)
        num_save_files: int
            number of separate savefiles to save result into using
            parallel processes. Improves performance and memory stability
            by reducing growing memory usage.
        num_dedupe_procs: int
            number of CPUs to dedicate to deduplication. For Javascript
            this should be around 1/4 to 1/3 of your CPUs as it is mostly
            duplicate code.
        compression: {lz4, gzip}
            choose compression algorithm to use. lz4 is extremely fast (10x gzip)
            but has a lower compression ratio.
        object_store_memory : int
            number of bytes for shared object store size
            (default set to 1/4 of system memory)
            If you start getting weird errors, try increasing this.
        max_calls : int
            The maximum number of times remote ray functions can be called
            before exiting.
            Set to 1 or a small number to control memory leaks caused by the
            observers, which is particularly important when using gitpython, but
            will in general slow
            things down as each task has a higher starting cost.
        """
        for obs in self.observers:
            obs.set_save_location(processed_dir=self.processed_dir, **kwargs)
        self.speak()
        num_workers = num_workers or 1024
        report_freq = kwargs.get("report_freq", 1024)
        # num_save_files = kwargs.get("num_save_files", 1)

        if not ray.is_initialized():
            # make object_memory_store 25% of total system memory, silence warnings
            if "object_store_memory" not in kwargs:
                kwargs["object_store_memory"] = psutil.virtual_memory().total // 4
            ray.init(
                object_store_memory=kwargs["object_store_memory"],
                num_cpus=num_cpus or psutil.cpu_count(),
            )

        dispatch = PipelineDispatch(self.observers, tasks, notify, **kwargs)
        dispatch_iter = iter(dispatch)

        try:
            dispatch.warmup(num_workers)
            with tqdm(total=len(tasks), position=1) as pbar:
                for result_id in dispatch_iter:
                    pbar.update(1)

                    _, error_msgs = ray.get(result_id)
                    for msg in error_msgs:
                        LOGGER.warning(msg)
                    if pbar.n % report_freq == 0:
                        report(
                            {"Statistics": dispatch.report_stats()},
                            print_stdout=True
                        )

            report({"Statistics": dispatch.report_stats()}, print_stdout=True)
            dispatch.save_dupe_report(self.processed_dir, **kwargs)

        except:
            LOGGER.info("Cleaning up! Please wait.")
            report({"Statistics": dispatch.report_stats()}, print_stdout=True)
            dispatch.save_dupe_report(self.processed_dir, **kwargs)
            raise
