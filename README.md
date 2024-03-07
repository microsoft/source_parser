# Source Parser

This package contains tools for parsing source code into annotated structural data structures: we extracted
import statements, global assignments, top-level methods, classes, class methods and attributes, and annotated
and separate each method and class into signature, docstring, body, and other language-specific attributes
for downstream modeling purposes. The tool provides a high-performance multiprocessing tool called `repocontext`
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

This package is available on the Data Science team's private PyPI, and it requires dependencies
which are only on the private PyPI. If you have never used Azure Artifacts, use the following two commands:

`python -m pip install --upgrade pip`
and
`python -m pip install keyring artifacts-keyring`

### PyPI installation

After following the above instructions, simply invoke

    python -m pip install source-parser --extra-index-url https://devdiv.pkgs.visualstudio.com/_packaging/DataScienceTools/pypi/simple/

Azure will prompt you with a code you can type into your browser to authenticate. If you are working on a
VM and it tries to open a web browser, kill the process and use `unset DISPLAY` to force web code authentication.


_Note: A common problem is that  `pip` asks for a username and password, and will not be satisfied by any input.
To overcome this, remove any `extra-index-url` from `~/.config/pip/pip.conf`, and follow the instructions again
from the beginning, being sure you installed `keyring` and `artifacts-keyring`._

### Local Installation from Source

Assuming you have `ssh` keys exchanged with Azure DevOps, clone via

    git clone https://devdiv.visualstudio.com/InternalTools/_git/source-parser

If you have already cloned the repo non-recursively, you can obtain the submodules by invoking

    git submodule update --init

Once all the code is present on your machine and the private package index is added, simply invoke

    python -m pip install -e . --extra-index-url https://devdiv.pkgs.visualstudio.com/_packaging/DataScienceTools/pypi/simple/

and follow the prompts to authenticate access to the private package index.

## Usage

### Scripting

Simply load the source file contents and hand to a parser, e.g.

```python
from source_parser.parsers import PythonParser
pp = PythonParser(open('source_parser/crawlercrawler.py').read())
print(pp.schema)
```

will print the schema extracted from `source_parser/crawlercrawler.py`.

### Parsing at scale

The real intention of this tool is to run massively at scale with 100s of thousands
of git repositories. If this is for you, you should install the CLI tools by invoking
```bash
python -m pip install source-parser-cli
```
The CLI tool  `repocontext` is added to your `PATH` upon installation, which can be used as follows

```bash
repocontext <language> <repo_list.json> <outdir> [--tmpdir <temporary_directory>]
```

where `<language>` is one of the supported languages indicated in the help message,
`<repo_list.json>` is a path to a `.json` file containin a list of dictionaries with at
least a `'url'` key for a `git` repository and optionally a `'license'` key. `<outdir>`
is the directory in which to place the saved results as a `lz4` compressed `jsonlines`
file, and `--tmpdir` is an optional place to save temporary data like cloned
repositories.

See [the `source-parser-cli` repository](https://dev.azure.com/devdiv/InternalTools/_git/source-parser-cli)
for more CLI tools and examples.

_Protip: mount a RAMdisk and hand it to `--tmpdir` to remove the IO bottleneck
and double parsing speeds! Further, you can set `outdir` to be in the RAMdisk as well, so no disk is necessary (if you have enough memory)._
```bash
sudo mount -t tmpfs -o size=<size in Gigabytes>G <name-ramdisk> /path/to/ramdisk`
```

### Reading the data

The default compression algorithm used is `lz4` for its high speed and reasonable
compression ratio. Because the data is highly compressible, and because there is a lot
of it, I recommend reading the data in an on-line fashion and not saving it all in memory
uncompressed at once. The JSON dictionaries are highly compressible so you can generally
expect the uncompressed data to be 2-3x as large.

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

## Adding new language support

We currently use the `athena_common` repository to manage `tree_sitter` grammars, and it
manages many common languages currently. Examine the parsers in the `source_parser/parsers` directory
and try to work by analogy in extracting the features of a new source code language. Be sure to
adhere to the schema!

# Data Schema

This is a description of the JSON schema into which `source-parser` will
transform source code files, for use in method and class-level code-natural
language modeling. The data will consist of JSON lines, that is valid JSON
separated by newline characters. Each line of JSON will be the features
extracted from a single source code file. The proposed JSON schema for each
individual file is as follows:

_NOTE: See individual language parsers in `source_parser/parsers` for the langauge-specific method and class attributes._

```json
{
	'file_name': 'name_of_file.extension',

    'file_hash': 'hash of file for literal deduplication',

	'relative_path': 'repo_top_level/path/to/file/name_of_file.extension',

	'repo_name': 'owner/repo-name',

    'commit-hash': 'hash of the commit being analyzed',

	'license': {
        'label': 'label provided by github API or in json list',
        'files': [
            'relative_path': 'path/to/license/file',
            'file_contents': 'license file contents',
        ],
    }

    'original_string': 'origina string of file',

	'file_docstring': 'string containing first docstring for all of file',

	'contexts': [
            'import statement 1',
            'import statement 2',
            'global variable expression 1',
            ...
        ],

	'language_version_details': [
        'e.g. python2 syntax detected', 'another languages idiosyncracies'
        ]

	'methods': [  # list of dictionaries annotating each method
		{
            'original_string': 'verbatim code of whole method',

            'byte_span': (start_byte, end_byte),

            'start_point': (start_line_number, start_column),

            'end_point': (end_line_number, end_column),

            'signature':
                'string corresponding to definition, name, arguments of method',

            'name': 'name of method',

            'docstring': 'verbatim docstring corresponding to this method',

            'body': 'verbatim code body',

            'original_string_normed':
                'code of whole method with string-literal, numeral normalization',

            'signature_normed': 'signature with string-literals/numerals normalized',

            'body_normed': 'code of body with string-literals/numerals normalized',

            'default_arguments': ['arg1': 'default value 1', ...],

            'syntax_pass': 'True/False whether the method is syntactically correct',

            'attributes': [
            	'language_specific_keys': 'language_specific_values',
                # e.g.
                'decorators': ['@wrap', '@abstractmethod'],
                ],
            ...
        },
        ...
	]

	'classes': [
        {
		'original_string': 'verbatim code of class',

        'byte_span': (start_byte, end_byte),

        'start_point': (start_line_number, start_column),

        'end_point': (end_line_number, end_column),

        'name': 'class name',

        'definition': 'class definition statement',

		'class_docstring': 'docstring corresponding to to-level class definition,

		'attributes': {  # language specific keys and values, e.g.
                'expression_statements': [
                    {
                      'expression': 'attribute = 1',
                      'comment': 'comment associated'
                    },
                'classes': [  # classes defined within classes
                    {
                        # same structure as classes
                    }
                ]
                ...
                ]
		    },

		'methods': [
            '# list of class methods of the same form as top-level methods',
            ...
            ]
	    }
    ...
    ]
]
```
# Development Tips
- Tree playground is useful for development and debugging: <https://tree-sitter.github.io/tree-sitter/playground>.
- ```pytest -s``` to show ```print``` statements during tests.
