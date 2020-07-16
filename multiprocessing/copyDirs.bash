#!/bin/bash

DIR="/home/caio/Downloads/v2013-core"
TGDIR="./makedirs"

for SUBDIR in $DIR/*/ ; do
	SUBDIR="${SUBDIR%\/*}"
	for i in {1..50} ; do
        cp -r "$SUBDIR" "${TGDIR}/$(basename "$SUBDIR")${i}"
	done
done
