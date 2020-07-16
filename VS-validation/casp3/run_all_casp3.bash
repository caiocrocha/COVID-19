#!/bin/bash

###################
# Config
###################
project="casp3.chemflow"
receptor="${project}/LigFlow/receptors/receptor.pdbqt"
reference_lig="${project}/LigFlow/compounds/crystal_ligand.mol2"

#################
# Cmd line parser
#################
prepare=0
config=0
run=0

while [[ "$#" -gt 0 ]]; do case $1 in
    -p|--prepare) prepare=1;;
    -c|--config) config=1;;
    -r|--run) run=1;;
    *) echo "Unknown parameter passed: $1"; exit 1;;
esac; shift; done

if [[ "${prepare}" = "0" && "${config}" = "0" && "${run}" = "0" ]] ; then
    echo "Nothing done here"
    exit 1
fi

###################
# Functions
###################
split_multi_molecule() {

if [ ! -d ${project}/LigFlow/compounds ] ; then
     mkdir -p ${project}/LigFlow/compounds
fi

cp casp3/${compounds} ${project}/LigFlow/compounds
compounds="${project}/LigFlow/compounds/${compounds}"
gunzip ${compounds}
compounds="${compounds%.gz}"

if [ ! -d ${project}/LigFlow/originals ] ; then
     mkdir -p ${project}/LigFlow/originals
fi

awk -v project="${project}/LigFlow/originals" '/@<TRIPOS>MOLECULE/{header=$1 ; getline ; filename=$1".mol2" ; print header > project/filename}; {print > project/filename}' "$compounds"

}

write_config() {
    args="$(bbox.py ${reference_lig})"
    args=($args)
    echo "receptor       = ${receptor}
center_x       = ${args[1]}
center_y       = ${args[3]}
center_z       = ${args[5]}
size_x         = ${args[7]}
size_y         = ${args[9]}
size_z         = ${args[11]}
num_modes      = 10
exhaustiveness = 8
energy_range   = 3.0
cpu            = 1"
}

###################
# Program
###################

if [ "${prepare}" = "1" ] ; then
    echo "Preparing"
    # Step 0 - Extract casp3.tar.gz file

    if [ ! -d casp3 ] && [ -f casp3.tar.gz ] ; then
        tar -xzf casp3.tar.gz
    fi

    # Step 1 - Split .mol2 compounds files

    if [ ! -d ${project}/LigFlow/originals ] ; then
        compounds="actives_final.mol2.gz"
        split_multi_molecule

        compounds="decoys_final.mol2.gz"
        split_multi_molecule

        # Remove duplicates
        for complex in ${project}/LigFlow/originals/* ; do
            mv "$complex" tmp
            awk -v complex="${complex}" '1;/@<TRIPOS>MOLECULE/{if (NR > 1) exit} {print > complex}' tmp
        done >/dev/null
        rm tmp
    fi


    # Step 2 - Prepare dockings
    # Open receptor with PyMOL (wrong molecule format)

    if [ ! -f ${receptor} ] ; then
        ${MGLTOOLS_BIN}/pythonsh ${MGLTOOLS_UTIL}/prepare_receptor4.py -r "${receptor%.*}.pdb" -o "${receptor}" -U nphs_lps_waters &
    fi

    for originals in ${project}/LigFlow/originals/* ; do 

        complex="$(basename ${originals})"
        complex="${complex%.*}"

        folder="${project}/DockFlow/qvina/${complex}"

        if [ ! -d ${folder} ] ; then
            mkdir -p ${folder}
        fi

        if [ ! -f ${folder}/ligand.pdbqt ]   ; then
            ${MGLTOOLS_BIN}/pythonsh ${MGLTOOLS_UTIL}/prepare_ligand4.py -l ${originals} -o ${folder}/ligand.pdbqt -U lps >/dev/null 2>&1 &
        fi 
     
    done

    wait
fi

if [ "${config}" = "1" ] ; then
    # Step 3 - Write config files for the jobs
    echo "Writing config files for the jobs"

    if [ ! -f ${reference_lig} ] ; then
        cp "casp3/$(basename ${reference_lig})" ${project}/LigFlow/compounds/
    fi

    write_config >${project}/qvina_config.in

    for folder in ${project}/DockFlow/qvina/* ; do
        complex="$(basename ${folder})"

        printf '#!/bin/bash
#$ -S /bin/bash
#$ -cwd
#$ -N %s
#$ -o %s/job.log
#$ -e %s/job.log
#$ -j y

EXEC="%s"
FOLDER="%s"
CONFIG="%s/qvina_config.in"

${EXEC} --ligand ${FOLDER}/ligand.pdbqt --out ${FOLDER}/out.pdbqt --log ${FOLDER}/out.log --config ${CONFIG} 
' "$complex" "$folder" "$folder" "${QVINA_EXEC}" "$folder" "$project" >${folder}/job.sh

    done
fi

if [ "${run}" = "1" ] ; then
    # Step 4 - Run dockings
    echo "Submitting jobs"

    for folder in ${project}/DockFlow/qvina/* ; do
        if [[ ! -f ${folder}/out.pdbqt && -f ${folder}/ligand.pdbqt && -f ${receptor} ]] ; then
            qsub -q all.q@compute-1* ${folder}/job.sh >/dev/null || exit 1
        else
            echo "Conflicts found: job '$(basename ${folder})' has already been run"
            read -r -p "Continue? [Y/n] " response
            case "$response" in
                [nN]|[nN][oO])
                    echo "Exiting"
                    exit 1
                    ;;
            esac

        fi

    done
fi
