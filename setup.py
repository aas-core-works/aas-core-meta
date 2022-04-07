"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""
import os
import sys

from setuptools import setup, find_packages

# pylint: disable=redefined-builtin

here = os.path.abspath(os.path.dirname(__file__))  # pylint: disable=invalid-name

with open(os.path.join(here, "README.rst"), encoding="utf-8") as fid:
    long_description = fid.read()  # pylint: disable=invalid-name

with open(os.path.join(here, "requirements.txt"), encoding="utf-8") as fid:
    install_requires = [line for line in fid.read().splitlines() if line.strip()]

setup(
    name="aas-core-meta",
    version="2022.4.30a1",
    description="Provide meta-models for Asset Administration Shell information model.",
    long_description=long_description,
    url="https://github.com/aas-core-works/aas-core-meta",
    author="Nico Braunisch, Marko Ristin, Marcin Sadurski",
    author_email="rist@zhaw.ch",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
    ],
    license="License :: OSI Approved :: MIT License",
    keywords="asset administration shell,design-by-contract,meta-model",
    packages=find_packages(exclude=["tests"]),
    install_requires=install_requires,
    # fmt: off
    extras_require={
        "dev": [
            "black==22.3.0",
            "mypy==0.910",
            "aas-core-codegen==0.0.6"
        ],
    },
    # fmt: on
    py_modules=["aas_core_meta"],
    package_data={"aas_core_meta": ["py.typed"]},
    data_files=[(".", ["LICENSE", "README.rst", "requirements.txt"])],
)
