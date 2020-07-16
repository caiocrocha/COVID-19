#!/usr/bin/env python
# coding: utf-8
# Config
#%%
'''
ChemFlow - Computational Chemistry WorkFlows

Module: 
ScoreFlow Delta Vina with gradient boost (DXGB)

Warning:
   By now, this Script only works to rescore DockFlow projects produced with VINA/Qvina/SMINA
   Future updates will enable rescoring arbitrary receptor.pdb + ligand(s).mol2 inputs. 

Install requirements:

    DXGB must be appropriately installed for this script to work
    Follow up their install instructions here:
    https://github.com/jenniening/deltaVinaXGB

    Make sure you test it ! ScoreFlow will use the DXGB environment
    "conda activate DXGB"
    
Note:
     Python paths are not set inside their scripts
     as a consequence DXGB MUST be executed from it's on folder

     cd /home/dgomes/github/deltaVinaXGB/DXGB/ 
     python run_DXGB.py --datadir /home/dgomes/my_project/my_complex --pdbid my_pdbid

Run requirements: 
At the "my_complex" folder, one must have several files:
    pdbid_protein.pdb
    pdbid_protein_all.pdb
    pdbid_ligand.sdf
'''

############################################################
# Imports                                                  #
############################################################
import sys
#sys.path.append('/home/dgomes/github/ChemFlow.py/ChemFlow/')  
from commom import *

import os
import pickle
import argparse
from progress.bar import Bar
import subprocess

############################################################
# Global Variables                                         #
############################################################
DXGB   = os.getenv('DXGB')


###########################################################
# Main program                                            #
###########################################################
def main() :

    write_header()

    arguments = get_cmd_line()

    # Assign arguments
    # General ChemFlow arguments
    project    = arguments['project']
    try :
        project = project.split('.chemflow')[0]
    except :
        pass
    project=project+'.chemflow'
    
    # Update dictionary
    arguments.update({'project': project})

    # Get ligand list and number of ligands.
    ligand_list = natsorted( get_ligand_list(arguments['project'],
                                             arguments['protocol'],
                                             arguments['compounds']) )

    # Create output dir.
    out_dir=os.path.join(arguments['project'],
                         'ScoreFlow',
                         arguments['protocol'],
                         'dxgb')

    os.makedirs(out_dir,exist_ok=True)

    # Setup calculations
    cmd_line = prepare_from_project(arguments['project'],
                                    arguments['protocol'],
                                    ligand_list,
                                    out_dir,
                                    arguments['first'],
                                    arguments['last'])

    print(cmd_line)
    
    quit()





###########################################################
# Functions                                               #
###########################################################
def prepare_from_project(project,protocol,ligand_list,out_dir,first,last) :

    out_dir=os.path.abspath(out_dir)
    # Create command line
    cmd_line=[]

    input_path  = os.path.join(project,'DockFlow',protocol)
    
    if os.path.isfile(os.path.join (input_path,'receptor.pdbqt') ) :
        receptor_file=os.path.join (input_path,'receptor.pdbqt')
        ligand_name='out.pdbqt'

    if os.path.isfile(os.path.join (input_path,'receptor.mol2') ) :
        receptor_file=os.path.join (input_path,'receptor.mol2')
        ligand_name='docked_ligands.mol2'
   
    # Convert receptor 
    os.system(f'obabel -ipdbqt {receptor_file} -opdb -O {out_dir}/receptor.pdb')

    for ligand in ligand_list : 

        ligand_file   = os.path.join(input_path,ligand,ligand_name)
        
        os.makedirs(os.path.join(out_dir,ligand,'poses'),exist_ok=True)

        filename_poses=os.path.join(out_dir,ligand,'poses','poses.pdb')
        os.system(f'obabel -ipdbqt {ligand_file} -f {first} -l {last}  -opdb -O {filename_poses}')
        os.system(f'obabel -ipdb  {filename_poses} -m  -opdb -O {filename_poses}')

        for pose in range(1,last+1) :
            os.makedirs(os.path.join(out_dir,ligand,str(pose)),exist_ok=True)
            os.system(f'mv     {out_dir}/{ligand}/poses/poses{pose}.pdb {out_dir}/{ligand}/{pose}/pdbid_ligand.pdb')
            os.system(f'ln -sf {out_dir}/receptor.pdb      {out_dir}/{ligand}/{pose}/pdbid_protein.pdb')
            os.system(f'ln -sf {out_dir}/receptor.pdb      {out_dir}/{ligand}/{pose}/pdbid_protein_all.pdb')
            os.system(f'ln -sf {DXGB}/RF20_rm2016.rda {out_dir}/{ligand}/{pose}/RF20_rm2016.rda')

            datadir=os.path.join(out_dir,ligand,str(pose))
            datadir=os.path.abspath(datadir)
            cmd_line.append(f'python {DXGB}/run_DXGB.py --datadir {datadir} --runfeatures --average --pdbid pdbid --runrf' )

        print(cmd_line)
        quit()
    return cmd_line



def get_cmd_line():
    parser = argparse.ArgumentParser(description = 'ScoreFlow - DeltaVina XGB')

    # General options
    parser.add_argument('--project',
                        action   = 'store',
                        dest     = 'project',
                        required = True,
                        help     = 'Project name.')

    parser.add_argument('--protocol',
                        action   = 'store',
                        dest     = 'protocol',
                        default  = 'default',
                        required = False,
                        help     = 'Protocol name.')

#    parser.add_argument('--docking-program',
#                        action   = 'store',
#                        dest     = 'docking',
#                        required = False,
#                        help     = 'Choose among: vina, qvina or plants')

    parser.add_argument('--first',
                        action   = 'store',
                        dest     = 'first',
                        default  = 3,
                        required = False,
                        type     = int,
                        help     = 'First pose to rescore')

    parser.add_argument('--last',
                        action   = 'store',
                        dest     = 'last',
                        default  = 1,
                        required = False,
                        type     = int,
                        help     = 'Last pose to rescore')

    parser.add_argument('--compounds',
                        action   = 'store',
                        dest     = 'compounds',
                        required = False,
                        help     = '.mol2 file containing docking poses to rescore')

    parser.add_argument('--verbose',
                        action   = 'store_true',
                        dest     = 'verbose',
                        required = False,
                        help     = 'Verbose mode')                        

    # Job control options
    parser.add_argument('--ncpus',
                        action   = 'store',
                        dest     = 'ncpus',
                        default  = '8',
                        type     = int,
                        required = False,
                        help     = 'Number of processors to user per HPC/local job [8]')

    # HPC job submission options
    parser.add_argument('--hpc',
                        action   = 'store',
                        dest     = 'HPC',
                        required = False,
                        help     = 'SGE, PBC, SLURM')

    parser.add_argument('--submit',
                        action   = 'store_true',
                        dest     = 'submit',
                        required = False,
                        help     = 'Submit to queue')

    parser.add_argument('--njobs',
                        action   = 'store',
                        dest     = 'njobs',
                        default  = '64',
                        type     = int,
                        required = False,
                        help     = 'Number of ligands per HPC job. [64]')
    
    arg_dict = vars(parser.parse_args())

    return arg_dict




if __name__ == "__main__":
    main()
