#!/bin/bash
# 
#########################
# COVID-19 Task force ! #
#########################
# 
# Manual docking and verification to validate Virtual Screening protocols.
#
#
################################# 
# Docking Program: QuickVina 02 #
#################################
#
#
# Juiz de Fora, Wed Mar 11 11:34:51 -03 2020  ! by dgomes.
#
# This folder contains evaluation of QuickVina02 parameters for Virtual Screening (VS)
# against 3-CL protein from SARS-CoV-2 (COVID-19).
# 
#
# "Docking Power" validation
# This refers to the capability of a scoring function to identify the native 
# ligand-binding pose among computer-generated decoys (other poses). Ideally, 
# the native binding pose should be ranked at the top. In CASF-2013, docking 
# power was evaluated through a 'self-docking' trial. [1]
# [1] Li, Y., Su, M., Liu, Z. et al. Assessing protein–ligand interaction scoring functions with the CASF-2013 benchmark. Nat Protoc 13, 666–680 (2018). https://doi.org/10.1038/nprot.2017.114

#####################################################################
# Input file preparation                                            #
#####################################################################
# 6lu7 biounit was downloaded from PDB and preprocessed using Maestro 2020 Academic.
# Maestro project: COVID-19/MAESTRO/6l7u/6lu7.prj 
# 
# The biounit was subject to PROPKA and sampling sidechains and water
# orientations to better represent the complex at pH 7.4
# 
# Individual .mol2 and .pdb files were generated for each component (naming is intuitive):
# complex, protein, chainA, chainB, ligandA, ligandB, water

#####################################################################
# Docking centers and dimensions                                    #
#####################################################################
# The AutoDock Tools 1.5.7 interface was used to define the docking 
# centers and search dimensions. Docking was centered on the ligands
# crystal structure centroid (geometic center) and sizes to their
# dimensions, respectively.
# 
# For PLANTS the search is spherical, so the largest dimension is used
# to define the sphere.
#
#####################################################################
# Summary of this experiment                                        #
#####################################################################
# Here we evaluate the hability of QuickVina 02 search function to 
# reproduce the original crystal structure (PDBid: 6LU7) of SARS-CoV-2
# 3-CL in complex with inhibitor.
# 
# Since it's bioactive for is a homodimer, where both chains contribute
# to each other's binding site, the full biounit was considered.
#
# The docking experiments will evaluate the "Docking Power" of AutoDock
# Vina, given variable search conditions in terms of "exhaustiveness" and
# "energy range" reporting, the first majorly interferes with the runtime.
#
# The crystal structure pose was used as starting point as well as a 
# dihedral randomized (without clashes) structure to remove the bias
# of provinding the "solution". This will aditionally evaluate the 
# performance of the search/scoring function to sample the ligand's
# conformational space.
#
# Notes from AutoDock Vina / QuickVina 02 manual.
# * exhaustiveness of the global search (roughly proportional to time)
# 
# * energy_range is the maximum energy difference between the best binding 
#                mode and the worst one displayed (kcal/mol)

# Config
#COVID_HOME=/home/dgomes/COVID-19/
#export PATH=${PATH}:/storage/BK_Computador_Chemflow/chemflow_home/software/qvina/bin/

# Base dir
BASEDIR=${PWD}

prepare_qvina() {

# Local optimization
if [ ! -f local.pdbqt ] ; then 
   qvina02 --receptor ../receptor.pdbqt --ligand crystal.pdbqt --out local.pdbqt  --log local.log    ${CENTER_SIZE} --local_only
fi

if [ ! -f random.pdbqt ] ; then 
   qvina02 --receptor ../receptor.pdbqt --ligand crystal.pdbqt --out random.pdbqt --log random.pdbqt ${CENTER_SIZE} --randomize_only
fi

for ligand in "crystal" "random" ; do 

    for run in 1 2 3 ; do

		# Loop over Exhaustiveness
        for ex in "8" "24" "32" ; do 

			# Loop over Energy ranges
            for er in "1" "3" ; do

              # Set file name
              name="${ligand}_redock_e${ex}_er${er}_${run}"

              # Run docking
         echo "qvina02 --receptor ../receptor.pdbqt \
                      --ligand ${ligand}.pdbqt \
                      --out ${name}.pdbqt  \
                      --log ${name}.log \
                      ${CENTER_SIZE} \
                      --exhaustiveness ${ex} \
                      --energy_range ${er} \
                      --cpu 1"

            done
        done
    done
done > dock.xargs

}

# Copy input files.
#cp ${COVID_HOME}/MAESTRO/6lu7/protein.pdb        .
#cp ${COVID_HOME}/MAESTRO/6lu7/ligandA_pH7.4.mol2 .
#cp ${COVID_HOME}/MAESTRO/6lu7/ligandB_pH7.4.mol2 .


# Prepare Receptor
if [ ! -f receptor.pdbqt ] ; then
    pythonsh $(command -v prepare_receptor4.py) -r protein.pdb -o receptor.pdbqt -U lps
fi

#####################################################################
# Run ligand chain A                                                #
#####################################################################
cd ${BASEDIR}
CENTER_SIZE='--center_x -9.732 --center_y 11.403 --center_z 68.455 --size_x 15.0 --size_y 21.0 --size_z 15.0 --num_modes 100'

if [ ! -d ligand_A ] ; then
    mkdir ligand_A
fi

# Go to working folder.
cd ${BASEDIR}/ligand_A

# Prepare Ligand Chain A
if [ ! -f crystal.pdbqt ] ; then
    pythonsh $(command -v prepare_ligand4.py) -l ../ligandA_pH7.4.mol2 -o crystal.pdbqt -U lps
fi

# Run experiment
prepare_qvina

# Run them all !!!
cat dock.xargs | xargs -P12 -I '{}' bash -c '{}' > dock.log


#####################################################################
# Run ligand chain B                                                #
#####################################################################
cd ${BASEDIR}
CENTER_SIZE='--center_x -33.315 --center_y 11.403 --center_z 25.768 --size_x 15.0 --size_y 21.0 --size_z 15.0 --num_modes 100'
if [ ! -d ligand_B ] ; then
    mkdir ligand_B
fi

# Go to working folder.
cd ${BASEDIR}/ligand_B

# Prepare Ligand Chain A
if [ ! -f crystal.pdbqt ] ; then
    pythonsh $(command -v prepare_ligand4.py) -l ../ligandB_pH7.4.mol2 -o crystal.pdbqt -U lps
fi

# Run experiment
prepare_qvina

# Run them all !!!
cat dock.xargs | xargs -P12 -I '{}' bash -c '{}' > dock.log
