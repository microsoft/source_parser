# Hierarchy

## Test file structure

- Test files should replicate the same folder structure as the repos, but under the `test` directory.

- Test files should start with `test_`. To avoid naming clashes while importing test modules, include the submodule path in the file name, without `source_parser`.

Example:
Test file for `source_parser/parsers/python_parser.py` should be at `test/source_parser/parsers/test_python_parser.py`
