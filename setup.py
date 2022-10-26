#! /usr/bin/env python3
#
# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from setuptools import setup
from setuptools import find_packages
import sys
import pathlib
import re

cwd = pathlib.Path(__file__).parent

readme_text = (cwd / "README.md").read_text()
requires_list = [
    "bitstruct >= 6.0.0",
    "argparse_addons",
    "PyInquirer",
    "jinja2",
    "python-can < 4.0",
    "can-isotp",
    "markdownify",
]

version_match = re.search(r"^__version__ = '(.*)'$",
                          (cwd / "odxtools" / "version.py").read_text(),
                          re.MULTILINE)
if version_match is None:
    print(f"Could not determine the odxtools version!")
    sys.exit(1)
version_string = version_match.group(1)

setup(name='odxtools',
      version=version_string,
      description='Utilities to work with the automotive diagnostics standard ODX.',
      long_description=readme_text,
      long_description_content_type='text/markdown',
      author='Katrin Bauer, Andreas Lauser',
      author_email='katrin.b.bauer@mbition.io, andreas.lauser@mbition.io',
      url='https://github.com/Daimler/odxtools',
      license='MIT',
      project_urls={
          'Bug Tracker': 'https://github.com/Daimler/odxtools/issues',
      },
      classifiers=[
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.8',
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: POSIX'
      ],
      keywords=['can', 'can bus', 'odx', 'pdx', 'obd', 'uds', 'automotive', 'diagnostics'],
      packages=find_packages(exclude=['tests']),
      python_requires='>=3.8',
      include_package_data=True,
      install_requires=requires_list,
      test_suite='tests',
      entry_points={
          'console_scripts': ['odxtools=odxtools.__init__:_main']
      })
