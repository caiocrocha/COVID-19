#!/bin/bash
#$ -S /bin/bash
#$ -cwd
#$ -N ZINC13757197
#$ -o /home/caiocedrola/Documentos/COVID-19/casp3.chemflow/DockFlow/qvina/ZINC13757197/job.log
#$ -e /home/caiocedrola/Documentos/COVID-19/casp3.chemflow/DockFlow/qvina/ZINC13757197/job.log
#$ -j y

EXEC="/home/caiocedrola/Downloads/qvina/bin/qvina02"
FOLDER="/home/caiocedrola/Documentos/COVID-19/casp3.chemflow/DockFlow/qvina/ZINC13757197"
CONFIG="/home/caiocedrola/Documentos/COVID-19/casp3.chemflow/qvina_config.in"

${EXEC} --ligand ${FOLDER}/ligand.pdbqt --out ${FOLDER}/out.pdbqt --log ${FOLDER}/out.log --config ${CONFIG} 
