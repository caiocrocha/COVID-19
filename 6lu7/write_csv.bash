#!/bin/bash

append_to_csv() {
if [ ! -f "docking.csv" ] ; then
    echo "Program,Ligand,Initial Pose,Pose,Exhaustiveness,Energy Range,Energy,RMSD,Execution" > "docking.csv"
fi

for file1 in ${dir}${initial_pose}_*.energy ; do
    base="${file1%.*}"
    file2="${base}.rmsd"        
    energy_range=0
    exh=0
    execution=0
    IFS='_' read -ra ADDR <<< "${file1%.*}"
    integer='^[0-9]+$'
    for substr in ${ADDR[@]}; do
        if [[ "$substr" == *"er"* ]] ; then
            energy_range="${substr#"er"}"
        elif [[ "$substr" == *"e"* && "${substr#"e"}" =~ $integer ]] ; then
            exh="${substr#"e"}"
        elif [[ $substr =~ $integer ]] ; then
            execution="$substr"
        fi
    done
    paste -d ',' $file1 $file2 | 
    awk -v data="$program,$lig,$initial_pose,$exh,$energy_range,$execution" '
        BEGIN { split(data,d,/,/); FS=OFS="," }
        { print d[1], d[2], d[3], FNR, d[4], d[5], $1, $2, d[6] }
        ' >> "docking.csv"
done

dir="vina/ligand_A/"
initial_pose="crystal"
program="Vina"
lig="A"
append_to_csv
initial_pose="random"
append_to_csv

dir="vina/ligand_B/"
initial_pose="crystal"
program="Vina"
lig="B"
append_to_csv
initial_pose="random"
append_to_csv

dir="qvina/ligand_A/"
initial_pose="crystal"
program="QVina"
lig="A"
append_to_csv
initial_pose="random"
append_to_csv

dir="qvina/ligand_B/"
initial_pose="crystal"
program="QVina"
lig="B"
append_to_csv
initial_pose="random"
append_to_csv
