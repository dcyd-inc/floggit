'''
# python function in/out logger

## Install

Requires Python 3

### Using pip

```
pip3 install floggit -U
```

### Using pipenv

```
pipenv install floggit
```

## Usage

### Simple monitoring

```python
from floggit import flog

@flog
def myfunc(*args, **kwargs):
    ...
    return result
```
'''

from setuptools import setup, find_packages

import floggit

setup(
    name="floggit",
    version=floggit.__version__,
    author="dcyd, inc.",
    author_email="info@dcyd.io",
    description="log function inputs and outputs at runtime",
    long_description=__doc__,
    long_description_content_type="text/markdown",
    url="https://github.com/dcyd-inc/floggit",
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
    ),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'google-cloud-logging>=3.0.0',
    ],
    tests_require=[
        'pytest',
    ],
    python_requires='>=3.9'
)
