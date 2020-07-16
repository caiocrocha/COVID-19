#!/bin/bash

base="/home/caiocedrola/Documentos/COVID-19"
project="${base}/casp3.chemflow"

run_vina() {
vina --local_only \
     --ligand ${filename} \
     --config ${project}/qvina_config.in
}

run_smina() {
smina --minimize \
      --ligand ${filename} \
      --config ${project}/qvina_config.in
}


run_smina_vinardo() {
smina --minimize --scoring vinardo \
      --ligand ${filename} \
      --config ${project}/qvina_config.in
}

get_score() {

awk -v LIGAND=${LIGAND} -v POSE=${POSE} 'BEGIN{OFS=",";}/Affinity/ {print LIGAND,POSE,$2}'

}

echo 'id,pose,vina'    >${base}/rescore_vina.csv
echo 'id,pose,smina'   >${base}/rescore_smina.csv
echo 'id,pose,vinardo' >${base}/rescore_vinardo.csv

for dir in ${project}/DockFlow/qvina/* ; do

  LIGAND="$(basename ${dir})"

  if [ ! -d ${dir}/poses ] ; then
      mkdir -p ${dir}/poses
  fi
  
  vina_split --input ${dir}/out.pdbqt --ligand ${dir}/poses/ >/dev/null 2>&1

  for filename in ${dir}/poses/* ; do
      POSE="$(basename $filename)"
      POSE="${POSE%.*}"

      run_vina | get_score >> rescore_vina.csv & 
      run_smina | get_score >> rescore_smina.csv & 
      run_smina_vinardo | get_score >> rescore_vinardo.csv &

      wait

  done

  rm -rf ${dir}/poses

done

