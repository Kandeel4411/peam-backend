## Supported Plagiarism Languages

This directory contains the currently supported languages for plagiarism detection. By default, JavaScript and Python are currently supported. To add a new languages, follow the steps below:

- **Add Tree-sitter language implementations**

    you'll need a Tree-sitter language implementation for the language that you want to parse. You can clone some of the existing language repos. i.e:

    ```bash
    ## In project root directory... ##

    git -C src/plagiarism/vendor/ https://github.com/tree-sitter/tree-sitter-go
    git -C src/plagiarism/vendor/ https://github.com/tree-sitter/tree-sitter-javascript
    git -C src/plagiarism/vendor/ https://github.com/tree-sitter/tree-sitter-python
    ```

- **Add language implementation path to settings**

    Go to [settings/base.py](../../core/settings/base.py) and modify the `PLAG_SUPPORTED_LANGAUGES` variable to add the paths to the languages implementations. i.e:

    ```python
    PLAG_SUPPORTED_LANGAUGES = [
        str(APPS_DIR / "plagiarism/vendor/tree-sitter-javascript"),
        str(APPS_DIR / "plagiarism/vendor/tree-sitter-python"),
        # Add paths here...
    ]
    ```

- **Modify `SupportedLanguages` class**

    Go to [plagiarism/sources.py](../sources.py) and modify the `SupportedLanguages` class to include the extensions and info of the languages.

    ```python
    class SupportedLanguages:
        """
        Structure that represents the supported languages for plagiarism
        """
        # Add languages here
        python: str = "python"
        javascript: str = "javascript"
        # Add languages extensions in the following dict
        exts: Dict[str, str] = {".py": python, ".js": javascript}
    ```

- **Modify `Dockerfile`**

  Go to [docker/Dockerfile](../../../docker/Dockerfile) and add the language implementations. i.e:

  ```Dockerfile
  ## Under the `dependencies` stage ##
  # -------------------------------- #
  # Go to `Cloning supported languages` section and add
  RUN git clone https://github.com/tree-sitter/tree-sitter-javascript
  RUN git clone https://github.com/tree-sitter/tree-sitter-python

- **Modify `setup_plagiarism.py` script**

  Go to [docker/scripts/setup_plagiarism.py](../../../docker/scripts/setup_plagiarism.py) and add the language implementations. i.e:

  ```python
  Language.build_library("build/languages.so", [
      "tree-sitter-python",
      "tree-sitter-javascript",
      # Add language here
  ])
  ```

- **Build the languages library**

    Run the following command to compile the language implementations

    ```bash
    ## In project root directory... ##
    poetry run python src/manage.py setup_plagiarism
    ```
