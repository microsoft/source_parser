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

### Data Schema

This is a description of the JSON schema into which `source_parser` will
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

            'signature': 'string corresponding to definition, name, arguments of method',

            'name': 'name of method',

            'docstring': 'verbatim docstring corresponding to this method',

            'body': 'verbatim code body',

            'original_string_normed': 'code of whole method with string-literal, numeral normalization',

            'signature_normed': 'signature with string-literals/numerals normalized',

            'body_normed': 'code of body with string-literals/numerals normalized',

            'default_arguments': ['arg1': 'default value 1', ...],

            'syntax_pass': 'True/False whether the method is syntactically correct',

            'attributes': [
            	'language_specific_keys': 'language_specific_values',
                'decorators': ['@wrap', '@abstractmethod'],
                ...
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

## Contributing

We welcome contributions. Please follow [this guideline](CONTRIBUTING.md).

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.

