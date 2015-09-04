#!/usr/bin/env python
import io

from setuptools import find_packages, setup


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

description = "Python tools for managing academic references."
long_description = read('README.rst')

url = "https://github.com/tbekolay/refs"
setup(
    name="refs",
    version="0.1.0",
    author="Trevor Bekolay",
    author_email="tbekolay@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    scripts=[],
    url=url,
    description=description,
    long_description=long_description,
    entry_points={
        'console_scripts': [
            'refs = refs.main:main',
        ]
    },
    install_requires=[
        'click',
    ],
)
