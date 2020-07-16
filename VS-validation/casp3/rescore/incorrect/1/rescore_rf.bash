#!/bin/bash

base=~/Documentos/COVID-19/VS-validation/casp3
project="${base}/casp3.chemflow"

# Create a single .pdbqt file adding ligand name, so RFScore_VS_v2 understands it.
if [ ! -f ${base}/all_out.pdbqt ] ; then
    for dir in ${project}/DockFlow/qvina/* ; do
        LIGAND="$(basename ${dir})"
        awk -v name="REMARK  Name = ${LIGAND}" '/MODEL/{print;print name;next}1' ${dir}/out.pdbqt

    done >${base}/all_out.pdbqt
fi

n_cpu=$(nproc --all)
let n_cpu=${n_cpu}-1

~/Downloads/rf-score-vs/rf-score-vs ${base}/all_out.pdbqt --receptor ${project}/LigFlow/receptors/receptor.pdbqt -i pdbqt -o csv -O ${base}/rfscore.csv --n_cpu ${n_cpu}
