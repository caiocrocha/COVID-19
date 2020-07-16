#!/bin/bash

[ -f ligand.lst ] || awk 'f{print;f=0} /MOLECULE/{f=1}' ../all_final.mol2 |uniq > ligand.lst

project=..

run_vina() {
vina --cpu 1 --local_only \
     --receptor ${project}/protein.pdbqt \
     --ligand ${filename} \
     --center_x -7.449 --center_y -15.106 --center_z -9.893 \
     --size_x 18.530 --size_y 18.022 --size_z 13.248
}

run_smina() {
smina --cpu 1 --minimize \
      --receptor ${project}/protein.pdbqt \
      --ligand ${filename} \
      --center_x -7.449 --center_y -15.106 --center_z -9.893 \
      --size_x 18.530 --size_y 18.022 --size_z 13.248
}


run_smina_vinardo() {
smina --cpu 1 --minimize --scoring vinardo \
      --receptor ${project}/protein.pdbqt \
      --ligand ${filename} \
      --center_x -7.449 --center_y -15.106 --center_z -9.893 \
      --size_x 18.530 --size_y 18.022 --size_z 13.248
}


echo 'id,pose,vina'    > rescore_vina.csv
echo 'id,pose,smina'   > rescore_smina.csv
echo 'id,pose,vinardo' > rescore_vinardo.csv

nrescore=$(wc -l ligand.lst|cut -d' ' -f1)
count=0

while read LIGAND ; do

  echo -en "${LIGAND}  ${count}/${nrescore} \r"

  vina_split --input ${project}/reni.chemflow/DockFlow/qvina/${LIGAND}/out.pdbqt --ligand /dev/shm/${LIGAND}_ &>/dev/null
  
  nposes=$(ls -1 /dev/shm/${LIGAND}_*.pdbqt | wc -l)

  for POSE in $(seq -w ${nposes}) ; do
      filename=/dev/shm/${LIGAND}_${POSE}.pdbqt
      if [ -f ${filename} ] ; then
          run_vina          | awk -v LIGAND=${LIGAND} -v POSE=${POSE} 'BEGIN{OFS=",";}/Affinity/ {print LIGAND,POSE,$2}' >> rescore_vina.csv    &
          run_smina         | awk -v LIGAND=${LIGAND} -v POSE=${POSE} 'BEGIN{OFS=",";}/Affinity/ {print LIGAND,POSE,$2}' >> rescore_smina.csv   &
          run_smina_vinardo | awk -v LIGAND=${LIGAND} -v POSE=${POSE} 'BEGIN{OFS=",";}/Affinity/ {print LIGAND,POSE,$2}' >> rescore_vinardo.csv
      fi
  done 

  wait 

  # Cleanup 
  for POSE in $(seq -w 10) ; do
      filename=/dev/shm/${LIGAND}_${POSE}.pdbqt
      if [ -f ${filename} ] ; then
          rm ${filename}
      fi
      filename=/dev/shm/${LIGAND}_${POSE}_out.pdbqt
      if [ -f ${filename} ] ; then
          rm ${filename}
      fi

  done 

  let count=${count}+1

done <ligand.lst
