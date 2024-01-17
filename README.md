# floggit
client for logging runtime function inputs and outputs

## Development

### Environment requirements

* Python 3.8.x is installed. See [pyenv](https://github.com/pyenv/pyenv)
* pipenv is installed. See [Install Pipenv](https://pipenv.pypa.io/en/latest/#install-pipenv-today )
* git is installed. See [Installing Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git )

### Distributing the package in PyPI

This process comes from [this turorial](https://packaging.python.org/tutorials/packaging-projects/).
1. Increment the version in `setup.py`, using [these rules](https://www.python.org/dev/peps/pep-0440/) (or newer).
2. Install/update some modules:

```bash
pipenv install --dev
```

3. From the directory containing `setup.py` (and _not_ in a virtual environment), create the wheel:

```bash
rm -rf build/ dist/
pipenv run python3 setup.py sdist bdist_wheel
```

4. Upload the wheel to PyPI:
```bash
pipenv run python3 -m twine upload dist/*
```
