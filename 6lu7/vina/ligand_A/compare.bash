#!/bin/bash

# Escreve o comando para o PyMol
echo "intra_rms compare" > pymol.pml

compare() {
# Para juntar 
echo "MODEL 0" > compare.pdbqt

cat crystal.pdbqt >> compare.pdbqt

echo "ENDMDL" >> compare.pdbqt

cat ${filename}.pdbqt >> compare.pdbqt


pymol compare.pdbqt -c pymol.pml | awk '/cmd.intra_rms/{print $2}' > ${filename}.rmsd

awk '/-----/{flag=1;next}/Writing/{flag=0}flag{print $2}' ${filename}.log > ${filename}.energy

}


file_list1="crystal_redock_e24_er1_1
crystal_redock_e24_er1_2
crystal_redock_e24_er1_3
crystal_redock_e24_er3_1
crystal_redock_e24_er3_2
crystal_redock_e24_er3_3
crystal_redock_e32_er1_1
crystal_redock_e32_er1_2
crystal_redock_e32_er1_3
crystal_redock_e32_er3_1
crystal_redock_e32_er3_2
crystal_redock_e32_er3_3
crystal_redock_e8_er1_1
crystal_redock_e8_er1_2
crystal_redock_e8_er1_3
crystal_redock_e8_er3_1
crystal_redock_e8_er3_2
crystal_redock_e8_er3_3"

file_list2="random_redock_e24_er1_1
random_redock_e24_er1_2
random_redock_e24_er1_3
random_redock_e24_er3_1
random_redock_e24_er3_2
random_redock_e24_er3_3
random_redock_e32_er1_1
random_redock_e32_er1_2
random_redock_e32_er1_3
random_redock_e32_er3_1
random_redock_e32_er3_2
random_redock_e32_er3_3
random_redock_e8_er1_1
random_redock_e8_er1_2
random_redock_e8_er1_3
random_redock_e8_er3_1
random_redock_e8_er3_2
random_redock_e8_er3_3"


for filename in ${file_list1} ${file_list2} ; do
    compare
done

