#!/bin/bash

[ -f ligand.lst ] || awk 'f{print;f=0} /MOLECULE/{f=1}' ../all_final.mol2 |uniq > ligand.lst

project=..

# Create a single .pdbqt file adding ligand name, so RFScore_VS_v2 understands it.
while read LIGAND ; do 
    awk -v name="REMARK  Name = ${LIGAND}" '/MODEL/{print;print name;next}1' ${project}/reni.chemflow/DockFlow/qvina/${LIGAND}/out.pdbqt
done <ligand.lst > all_out.pdbqt

#~/software/rf-score-vs/rf-score-vs --receptor ${project}/protein.pdbqt -i pdbqt -o csv -O rfscore.csv --n_cpu 6 all_out.pdbqt
