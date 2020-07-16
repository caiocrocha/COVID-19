# Install miniconda3

# Create an environment to run ChemFlow
conda create -n chemflow

# Activate the environment
conda activate chemflow

# Install the required software
conda install -y progress
conda install -y pandas
conda install -y seaborn
conda install -y -c bioconda mgltools
conda install -y -c bioconda autodock-vina
conda install -y -c bioconda smina

# ODDT provides VinaRF scoring functions
conda install -y -c oddt oddt

# General molecule conversion
conda install -y -c openbabel openbabel

# RDKit
conda install -y -c rdkit rdkit

# AmberTools allows MM(PB,GB)SA rescoring.
conda install -y -c ambermd  ambertools


