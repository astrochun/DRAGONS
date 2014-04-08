#!/bin/bash

sourcedir='../../../../astrodata/doc/rs_UsersManual'

if [ ! -e conf.py ]; then
    ln -s ${sourcedir}/*.rst .
    ln -s ${sourcedir}/appendices .
    rm index.rst
    rm index-latex.rst
else
    echo 'cd to the instrument directory'
fi

