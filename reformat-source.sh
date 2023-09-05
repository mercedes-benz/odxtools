#! /bin/sh
#
# This script brings the style of all python code within the odxtools
# director into conformance the style mandated for the odxtool
# project. Before you open a pull request, run it on your working
# copy. (You need to have yapf with toml support and isort installed:
#
# pip3 install yapf isort toml
#
if ! test -f odxtools/database.py || \
   ! test -d tests || \
   ! test -d examples; then

    echo "You need to run this script in the topmost directory" >&2
    echo "of a working copy of odxtools." >&2
    exit 1
fi

isort -l 100 -m VERTICAL odxtools tests examples
yapf -r -i odxtools/ tests/ examples/
