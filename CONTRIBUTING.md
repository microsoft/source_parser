# Contribution Guidelines


## Contributing

To contribute, branch source-parser and file a [pull request](https://github.com/microsoft/source_parser/pulls).

### Develop, Build, Deploy and Test locally
  - Use Python 3.11-3.14 with a C/C++ compiler and Python development headers.
    Tree-sitter 0.26.x is the supported bindings line.
  - Clone source:

      ```bash
      git clone https://github.com/microsoft/source_parser
      ```

      If you have already cloned the repo non-recursively, you can obtain the `treesitter` submodules by invoking

      ```bash
      git submodule update --init --recursive
      ```
  - Install an editable development build (this compiles the pinned grammars):
      ```bash
            python -m pip install --upgrade pip
            python -m pip install build pylint pytest "setuptools>=77"
            python -m pip install -e .
      ```
  - Execute `python -m pytest test/` in the root directory and ensure all tests pass.
    Reinstall the editable build after changing native grammar sources.
  - Run `python -m build` to produce a source distribution and native wheel.
    The grammar bindings use CPython's stable ABI with a Python 3.11 minimum.
    Release automation uses cibuildwheel for portable Linux/macOS wheels;
    source distributions include the grammar sources for other supported Unix platforms.
  - PR CI exercises Python 3.11-3.14 on Linux and Python 3.14 on macOS. It runs
    the tests outside the checkout against the installed wheel, so missing
    grammar bindings or package data cannot be hidden by the source tree.
  - Bump the version number in the `source_parser/_version.py` file
     following semantic versioning
  - If you modify the schema, try to modify it in a way which does not
     break backwards compatibility and be sure to update the README.md
     description of the schema.

### Publishing a release

Update `source_parser/_version.py` to a new version and merge the change before
manually running **Release and Publish pipeline** from GitHub Actions on the
ref to release. The workflow builds the distributions, publishes them to PyPI,
then creates a GitHub Release named `source-parser <version>` with a
`v<version>` tag at the exact workflow commit. The GitHub Release includes
generated release notes and the same wheels and source archive published to PyPI.

Only the GitHub Release job has `contents: write`; PyPI publication continues to
use trusted publishing with `id-token: write`. Existing tags must point to the
workflow commit. The workflow never moves tags or overwrites existing releases.

If GitHub Release creation fails after PyPI publication succeeds, use
**Re-run failed jobs** rather than rerunning the successful PyPI job. If a
partially created release draft already exists, finish that draft instead of
rerunning release creation.

### Adding new language support

Examine the parsers in the `source_parser/parsers` directory
and try to work by analogy in extracting the features of a new source code language. Be sure to
adhere to the schema!

Add the pinned grammar submodule under `source_parser/tree_sitter/assets` and
register its language name and exported C symbol in
`source_parser/tree_sitter/grammars.json`. The build creates a native capsule
binding for every registered grammar. Keep snapshots compatible with
Tree-sitter 0.26's supported grammar ABI range and run the grammar-loading and
parser-schema tests before updating a snapshot.

### Development Tips
- Tree playground is useful for development and debugging: <https://tree-sitter.github.io/tree-sitter/playground>.
- ```pytest -s``` to show ```print``` statements during tests.

### Linting and formatting in VSCode

In VSCode, you may install the following extensions to support linting and formatting:

- [Pylint](https://marketplace.visualstudio.com/items?itemName=ms-python.pylint)
- [autopep8](https://marketplace.visualstudio.com/items?itemName=ms-python.autopep8)

Linting is enabled and configured in [settings.json](./.vscode/settings.json) using `Pylint`, as well as auto-formatting on save using `autopep8`.

You may disable linting rules for specific lines/files in cases where the linting suggestion doesn't make sense.

You may also run linting at the repo root directory (which are the same commands in PR validation):

```
python -m pip install pylint "setuptools>=77"
pylint source_parser test/source_parser setup.py --recursive=y
```

Setuptools must be installed in the lint environment so pylint can import it
from `setup.py`. Dependencies installed by an isolated package build are not
available to the linter.

## Reporting Issues

If you encounter any issues, please open an [issue](https://github.com/microsoft/source_parser/issues).

## Contributor License Agreement

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
