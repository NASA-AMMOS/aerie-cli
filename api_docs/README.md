# **Auto-documentation for Aerie-CLI API:**

The Aerie-CLI API provides a user-extendable API for interacting with an instance of Aerie. 

The following steps generate documentation for the files in `src/aerie_cli` (excluding the `/command` directory and `app.py`). 

<br>

## **How to Generate Documentation Using Sphinx-CLI**
1. Make sure you have `sphinx` is installed: 

    ```
    pip install sphinx
    ```

2. Navigate to the outer `aerie-cli` directory: 
    ```
    cd aerie-cli
    ```

3. Using [`sphinx-apidoc`](https://www.sphinx-doc.org/en/master/man/sphinx-apidoc.html), generate the for files in `src/aerie_cli` into the `api_docs` directory.  
    ```
    sphinx-apidoc -o ./api_docs/source ./src/aerie_cli
    ```

4. View this documentation with the `index.html` file located in `api_docs/build/html`.

<br>

## **Modify the Documentation Output**
To edit the format of the html output, you can modify the following files using the directives from the sphinx `autodoc` extension ([`sphinx.ext.autodoc`](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html)): 

1. [`aerie_cli.rst`](source/aerie_cli.rst): Contains files in the src/aerie_cli directory (excluding app.py). Lists subpackages as aerie_cli.schemas and aerie_cli.utils. 
2. [`aerie_cli.schemas.rst`](source/aerie_cli.schemas.rst): Contains the files in the src/aerie_cli/schemas directory. 
3. [`aerie_cli.utils.rst`](source/aerie_cli.schemas.rst): Contains the files in the src/aerie_cli/utils directory. 

<br>

## **Format Docstrings**
Sphinx autodoc can correctly generate docs from two formatting options: 

1. Follow the [Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html). Many of the docstrings already in the app follow this style. 
2. Or, an alternative is following the [Sphinx Docstring format](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html).
