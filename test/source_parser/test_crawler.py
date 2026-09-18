# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from unittest.mock import MagicMock, Mock, sentinel

import pytest

from source_parser.cli import crawler


@pytest.fixture(name="ray_runtime")
def mock_ray_runtime(monkeypatch):
    runtime = Mock(spec=crawler.ray)
    runtime.is_initialized.return_value = False
    runtime.get.return_value = ({}, [])
    monkeypatch.setattr(crawler, "ray", runtime)
    return runtime


@pytest.fixture(name="dispatch")
def mock_dispatch(monkeypatch):
    pipeline = MagicMock(spec=crawler.PipelineDispatch)
    pipeline.__iter__.return_value = iter([sentinel.result])
    pipeline.report_stats.return_value = {"tasks_finished": 1}
    monkeypatch.setattr(crawler, "PipelineDispatch", Mock(return_value=pipeline))
    return pipeline


@pytest.mark.parametrize("num_cpus", [None, 3])
@pytest.mark.parametrize("object_store_memory", [None, 128 * 1024**2])
def test_map_starts_cpu_only_ray(
    monkeypatch, tmp_path, ray_runtime, dispatch, num_cpus, object_store_memory,
):
    monkeypatch.setattr(crawler.psutil, "cpu_count", Mock(return_value=8))
    monkeypatch.setattr(crawler.psutil, "virtual_memory", Mock(return_value=Mock(total=1024**3)))
    options = {} if object_store_memory is None else {"object_store_memory": object_store_memory}
    observer = Mock()

    crawler.CrawlCrawler([observer], tmp_path).map(
        [{"url": "test-repository"}], num_cpus=num_cpus, num_workers=2, **options,
    )

    ray_runtime.init.assert_called_once_with(
        object_store_memory=object_store_memory or 1024**3 // 4,
        num_cpus=num_cpus or 8,
        num_gpus=0,
    )
    observer.set_save_location.assert_called_once_with(processed_dir=tmp_path, **options)
    dispatch.warmup.assert_called_once_with(2)
    ray_runtime.get.assert_called_once_with(sentinel.result)
    dispatch.save_dupe_report.assert_called_once()


def test_map_preserves_existing_ray_runtime(tmp_path, ray_runtime, dispatch):
    ray_runtime.is_initialized.return_value = True

    crawler.CrawlCrawler([], tmp_path).map(
        [{"url": "test-repository"}], num_cpus=3, num_workers=2, object_store_memory=128 * 1024**2,
    )

    ray_runtime.init.assert_not_called()
    dispatch.warmup.assert_called_once_with(2)
    ray_runtime.get.assert_called_once_with(sentinel.result)


def test_map_propagates_ray_startup_errors(tmp_path, ray_runtime, dispatch):
    ray_runtime.init.side_effect = RuntimeError("Ray startup failed")

    with pytest.raises(RuntimeError, match="Ray startup failed"):
        crawler.CrawlCrawler([], tmp_path).map(
            [], num_cpus=1, object_store_memory=128 * 1024**2,
        )

    dispatch.warmup.assert_not_called()
