#!/bin/bash

for line in $(cat .env)
do
  export $line
done

python shogun_web.py
