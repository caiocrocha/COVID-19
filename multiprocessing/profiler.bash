#!/bin/bash

while [[ "$#" -gt 0 ]]; do case $1 in
  -n|--number) NUM="$2"; shift;; # number of subdirectories
  -e|--execution) EXE="$2"; shift;; # execution number
  *) echo "Unknown parameter passed: $1"; exit 1;;
esac; shift; done

if [ ! -f "times.csv" ] ; then
	echo "EXECUTION,SUBDIRS,SERIAL,PARALLEL(4)" > "times.csv"
fi

echo "${EXE},${NUM},$(python fileExists.py),$(python fileExists_thread.py)" >> "times.csv"
