#!/bin/bash

cat .env | while read line
do
  echo $line
  heroku config:set $line
done
