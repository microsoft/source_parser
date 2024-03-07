# Contribution Guidelines


## Contributing

To contribute, branch source-parser and file a [pull request](https://github.com/microsoft/source_parser/pulls).

### When submitting a PR you must take care to do two things
  1. Excecute `pytest test/` in the root directory and ensure
     all the tests pass
  2. Bump the version number in the `source_parser/_version.py` file
     following semantic versioning
  3. If you modify the schema, try to modify it in a way which does not
     break backwards compatibility and be sure to update the README.md
     description of the schema.

### Linting and formatting in VSCode

In VSCode, you may install the following extensions to support linting and formatting:

- [Pylint](https://marketplace.visualstudio.com/items?itemName=ms-python.pylint)
- [Flake8](https://marketplace.visualstudio.com/items?itemName=ms-python.flake8)
- [autopep8](https://marketplace.visualstudio.com/items?itemName=ms-python.autopep8)

Linting is enabled and configured in [settings.json](./.vscode/settings.json) using `Pylint` and `Flake8`, as well as auto-formatting on save using `autopep8`.

You may disable linting rules for specific lines/files in cases where the linting suggestion doesn't make sense.

You may also run linting at the repo root directory (which are the same commands in PR validation):

```
pylint ./ --recursive=y
flake8 ./
```

## Reporting Issues

If you encounter any issues, please open an [issue](https://github.com/microsoft/Tokenizer/issues).

## Contributor License Agreement

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

