#!/bin/bash
#$ -S /bin/bash
#$ -cwd
#$ -N ZINC40516962
#$ -o /home/caiocedrola/Documentos/COVID-19/casp3.chemflow/DockFlow/qvina/ZINC40516962/job.log
#$ -e /home/caiocedrola/Documentos/COVID-19/casp3.chemflow/DockFlow/qvina/ZINC40516962/job.log
#$ -j y

EXEC="/home/caiocedrola/Downloads/qvina/bin/qvina02"
FOLDER="/home/caiocedrola/Documentos/COVID-19/casp3.chemflow/DockFlow/qvina/ZINC40516962"
CONFIG="/home/caiocedrola/Documentos/COVID-19/casp3.chemflow/qvina_config.in"

${EXEC} --ligand ${FOLDER}/ligand.pdbqt --out ${FOLDER}/out.pdbqt --log ${FOLDER}/out.log --config ${CONFIG} 
