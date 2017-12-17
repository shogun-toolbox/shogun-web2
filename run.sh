#!/bin/bash

source env/bin/activate
export FLASK_APP=shogun_web.py
export NOTEBOOKDIR=../shogun/doc/ipython-notebooks/

python shogun_web.py
