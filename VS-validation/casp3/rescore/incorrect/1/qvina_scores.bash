#!/bin/bash

project="casp3.chemflow"
output_file="qvina.csv"

echo "id,pose,qvina" > ${output_file}

ligands="$(ls ${project}/DockFlow/qvina/)"

for LIGAND in $ligands ; do
    awk -v LIGAND="${LIGAND}" $'/-----/{flag=1;next}/Writing/{flag=0}BEGIN{OFS=","}flag{print LIGAND,$1,$2}' ${project}/DockFlow/qvina/${LIGAND}/out.log

done >>${output_file}
