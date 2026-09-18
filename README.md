# Source Parser

This package contains tools for parsing source code into annotated json data structure: we extracted
import statements, global assignments, top-level methods, classes, class methods and attributes, and annotated
and separate each method and class into signature, docstring, body, and other language-specific attributes
for downstream modeling purposes. The tool provides a high-performance multiprocessing tool called `repo_parse`
which is capable of cloning and performing this parsing for all files in a repository at the rate of thousands
of repositories per minute. See subsequence sections for installation, usage, and at the end a general
description of the structural annotated schema.

## Currently supported languages
 * Python
 * Java
 * Javascript/Typescript
 * C#
 * C++
 * Ruby

## Installation

__NOTE__: this tool is only supported on a **NIX-style OS (Linux, MacOS, FreeBSD, etc)**

Source Parser 2.x supports **Python 3.11-3.14** and **Tree-sitter 0.26.x**
(`tree-sitter>=0.26,<0.27`). Python 3.10 and older and the legacy Tree-sitter
bindings are no longer supported.

Grammar snapshots are pinned in the repository and compiled into native
bindings when the package is built. Installing a compatible wheel requires no
C/C++ compiler or writable Tree-sitter grammar cache. Building from a source distribution
requires a C/C++ toolchain and Python development headers; see
[CONTRIBUTING.md](CONTRIBUTING.md) for checkout builds.

### Migrating from 1.x

The parser schema and pinned grammar snapshots are retained. Supported Python
**runtime** versions do not imply that every new Python syntax feature is
recognized by the pinned Python grammar. Python 2 source conversion remains
available through Fissix instead of the removed standard-library `lib2to3`.

`get_language("python")` and `get_language(LanguageId.PYTHON)` continue to work.
Runtime `build_library()` and the `force_build` argument to `get_language()`
have been removed; rebuild/reinstall the package after changing a grammar.
Custom Tree-sitter parsers should use `Parser(get_language("python"))` or assign
`parser.language`, rather than calling the removed `parser.set_language()`.

### PyPI installation

After following the above instructions, simply invoke

```bash
python -m pip install source-parser
```

## Usage

### Scripting

Simply load the source file contents and hand to a parser, e.g.

```python
from source_parser.parsers import PythonParser
pp = PythonParser(open('source_parser/crawler.py').read())
print(pp.schema)
```

will print the schema extracted from `source_parser/crawler.py`.

### Parsing at scale

The real intention of this tool is to run massively at scale with 100s of thousands
of git repositories. 
Two CLI tools are added upon installation:
 - `repo_parse -h`: semantically parses code using `source_parser`
 - `repo_scrape -h`: just grabs all files matching some patterns

Both commands start a CPU-only Ray runtime (`num_gpus=0`). This avoids GPU
device-name detection, which can fail on some NVIDIA/WSL setups. An already
initialized Ray runtime is reused unchanged.

for example:

```bash
repo_parse <language> <repo_list.json> <outdir> [--tmpdir <temporary_directory>]
```

where `<language>` is one of the supported languages indicated in the help message,
`<repo_list.json>` is a path to a `.json` file containin a list of dictionaries with at
least a `'url'` key for a `git` repository and optionally a `'license'` key. `<outdir>`
is the directory in which to place the saved results as a `lz4` compressed `jsonlines`
file, and `--tmpdir` is an optional place to save temporary data like cloned
repositories.

_Protip: mount a RAMdisk and hand it to `--tmpdir` to remove the IO bottleneck
and double parsing speeds! Further, you can set `outdir` to be in the RAMdisk as well, 
so no disk is necessary (if you have enough memory).

```bash
sudo mount -t tmpfs -o size=<size in Gigabytes>G <name-ramdisk> /path/to/ramdisk`
```


### Reading the data

The default compression algorithm used is `lz4` for its high speed and reasonable
compression ratio. Because the data is highly compressible, DO read the data in streaming
fashion and not saving it all in memory uncompressed at once. The JSON dictionaries are 
highly compressible so you can generally expect the uncompressed data to be 2-3x as large.

To this end there is a nice tool in `source_parser/__init__.py`, importable
via `from source_parser import load_zip_json`, which returns an iterator object
which uncompresses and returns only one file-level schema dictionary at a time.

To use:

```python
from source_parser import load_zip_json
for example in load_zip_json('file_saved_from_repocontext.lz4'):
    process_file_example(example)
```

If you'd like to load it all into memory at once:
```python
from source_parser import load_zip_json
all_data = list(load_zip_json('file_saved_from_repocontext.lz4'))
```

### Deduplicating code

`CodeDeduper` detects near-duplicate code using fingerprints of identifiers and
literals. The package uses `datasketch` 1.x to preserve compatibility with
existing fingerprints and duplicate-detection behavior. When adding a code
string immediately after querying it, use `new_hash=False` to reuse those
fingerprints without parsing and hashing the same code again:

```python
from source_parser.deduper import CodeDeduper

deduper = CodeDeduper(language="python")
unique_code = []
for code in code_strings:
    if not deduper.query(code):
        deduper.add(code, new_hash=False)
        unique_code.append(code)
```

Only use `new_hash=False` when the most recent query was for the same code
string. Otherwise, use `add(code)` to compute fresh fingerprints.

### Data schema

`source_parser` emits one JSON object per source file. `repo_parse` writes
these objects as [JSON Lines](https://jsonlines.org/) (one object per line),
optionally compressed with LZ4 or gzip.

There are two layers to the output:

1. Every language parser returns the common file-level fields described below.
2. `repo_parse` adds repository and source-file metadata. `repo_scrape` emits
   only this metadata and the original source; it does not add parsed methods or
   classes.

The project emits a family of language-specific schemas rather than one strict
cross-language JSON Schema. Method, class, and `attributes` fields reflect the
constructs available in each language. Consumers should rely on the common
file-level fields and treat declaration-specific fields as language-dependent.

#### Example `repo_parse` record

This abbreviated record shows the serialized JSON shape for a Python file.
Positions are zero-based, byte spans are end-exclusive, and Python tuples are
serialized as JSON arrays.

```json
{
  "url": "https://github.com/example/project",
  "repo_name": "example/project",
  "commit_hash": "0123456789abcdef0123456789abcdef01234567",
  "relative_path": "src/greeting.py",
  "original_string": "import math\n\nclass Greeter:\n    def greet(self, name=\"world\"):\n        return f\"Hello, {name}!\"\n",
  "file_hash": "e4a1c4c66a1da64278933d0a2529e0dde46594d76fdeacca3de409f1eaf3aef7",
  "file_docstring": "",
  "contexts": [
    "import math"
  ],
  "methods": [],
  "classes": [
    {
      "name": "Greeter",
      "definition": "class Greeter:",
      "class_docstring": "",
      "original_string": "class Greeter:\n    def greet(self, name=\"world\"):\n        return f\"Hello, {name}!\"",
      "byte_span": [13, 95],
      "start_point": [2, 0],
      "end_point": [4, 32],
      "attributes": {},
      "methods": [
        {
          "name": "greet",
          "signature": "    def greet(self, name=\"world\"):",
          "docstring": "",
          "body": "        return f\"Hello, {name}!\"",
          "original_string": "    def greet(self, name=\"world\"):\n        return f\"Hello, {name}!\"",
          "byte_span": [32, 95],
          "start_point": [3, 4],
          "end_point": [4, 32],
          "default_arguments": {
            "name": "\"world\""
          },
          "syntax_pass": true,
          "attributes": {}
        }
      ]
    }
  ],
  "license": {
    "label": "MIT",
    "files": [
      {
        "relative_path": "LICENSE",
        "file_contents": ""
      }
    ]
  }
}
```

#### File-level fields

| Field | Produced by | Type | Description |
| --- | --- | --- | --- |
| `file_hash` | parser, `repo_parse`, `repo_scrape` | string | Deterministic SHA-256 identifier derived from the source contents. |
| `file_docstring` | parser, `repo_parse` | string | Leading file comment or docstring, if recognized by the language parser. |
| `contexts` | parser, `repo_parse` | array of strings | File-level imports, assignments, or analogous language context. |
| `methods` | parser, `repo_parse` | array of objects | Top-level callable declarations recognized by the language parser. |
| `classes` | parser, `repo_parse` | array of objects | Top-level classes or analogous type declarations. |
| `original_string` | `repo_parse`, `repo_scrape` | string | Full source text, after any parser preprocessing. |
| `relative_path` | `repo_parse`, `repo_scrape` | string | File path relative to the repository root. |
| `url` | `repo_parse`, `repo_scrape` | string | Repository URL from the input task. |
| `repo_name` | `repo_parse`, `repo_scrape` | string | Repository owner and name derived from `url`. |
| `commit_hash` | `repo_parse`, `repo_scrape` | string | Commit parsed by the crawler. |
| `license` | `repo_parse`, `repo_scrape` | object | Input license label and discovered license-file paths. `file_contents` is currently empty. |

#### Declaration fields

Method and class objects commonly use the following fields, but availability
and exact meaning vary by language:

| Field | Type | Description |
| --- | --- | --- |
| `name` | string | Declaration name. |
| `original_string` | string | Source text covered by the declaration. |
| `byte_span` | two-integer array | UTF-8 byte offsets `[start, end)`. |
| `start_point` / `end_point` | two-integer array | Zero-based `[line, column]` Tree-sitter positions. |
| `signature` | string | Callable declaration without its body. |
| `definition` | string | Class/type declaration without its body. |
| `docstring` / `class_docstring` | string | Associated documentation when recognized. Some parsers use `docstring` for classes. |
| `body` | string | Declaration body when the parser exposes it. |
| `default_arguments` | object | Mapping from parameter source text to default-value source text. |
| `syntax_pass` | boolean | Whether Tree-sitter reports the declaration as syntactically valid. |
| `methods` / `classes` | array of objects | Nested declarations where supported. |
| `attributes` | object | Language-specific metadata such as decorators, modifiers, return types, fields, properties, bases, namespaces, or nested classes. |

For exact language-specific keys, see the parser implementations in
[`source_parser/parsers`](source_parser/parsers) and their corresponding tests
in [`test/source_parser/parsers`](test/source_parser/parsers).

## Contributing

We welcome contributions. Please follow [this guideline](CONTRIBUTING.md).

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
