#!/usr/bin/env python3
# coding: utf-8
# Config
"""
ChemFlow - Computational Chemistry WorkFlows

Script: DockFlow.py

This executes docking using either Autodock Vina (and variants) or PLANTS

It is assumed that you're following ChemFlow standard.

This script requires `argparse` to be installed within the Python environment
you are running this script in.

This file cannot be imported as a module yet, it needs "get_cmd_line".

It contains the following functions:
 
    * get_cmd_line - Returns the command line arguments containing i/o files
    * get_energy   - Read an autodock Vina/Smina/Qvina .log output file
    * main         - the main function of the script

This is part of ChemFlow.cc 
"""

############################################################
# Imports                                                  #
############################################################


import os 
import subprocess
from progress.bar import Bar
import argparse
import pickle

# Get the ChemFlow path and append to "path" so I can import modules (.py files)
import sys
sys.path.append(os.path.dirname(__file__))
from commom import *



############################################################
# Global Variables                                         #
############################################################
#PLANTS_EXEC   = '/home/dgomes/software/PLANTS/PLANTS1.2_64bit'
#SPORES_EXEC   = '/home/dgomes/software/PLANTS/SPORES_64bit'
#VINA_EXEC     = '/home/dgomes/software/autodock_vina_1_1_2_linux_x86/bin/vina'
#QVINA_EXEC    = '/home/dgomes/software/qvina/bin/qvina02'
#MGLTOOLS_BIN  = '${HOME}/home/dgomes/software/mgltools_x86_64Linux2_1.5.6/bin/'
#MGLTOOLS_UTIL = '/home/dgomes/software/mgltools_x86_64Linux2_1.5.6/MGLToolsPckgs/AutoDockTools/Utilities24/'

# Get environment variables
MGLTOOLS_BIN  = os.getenv('MGLTOOLS_BIN')
MGLTOOLS_UTIL = os.getenv('MGLTOOLS_UTIL')
VINA_EXEC     = os.getenv('VINA_EXEC')
QVINA_EXEC    = os.getenv('QVINA_EXEC')
PLANTS_EXEC   = os.getenv('PLANTS_EXEC')
SPORES_EXEC   = os.getenv('SPORES_EXEC')

############################################################
# Functions                                                #
############################################################

def main () :

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

    # Update dimensions
    ref_ligand = arguments['ref_ligand']
    if ref_ligand is not None :
        center_x,center_y,center_z,size_x,size_y,size_z = binding_box(
                arguments['ref_ligand'], arguments['padding'])
        arguments.update({'center_x': center_x})
        arguments.update({'center_y': center_y})
        arguments.update({'center_z': center_z})
        arguments.update({'size_x': size_x})
        arguments.update({'size_y': size_y})
        arguments.update({'size_z': size_z})
        
    # Update dimensions
    size_x,size_y,size_z,radius=set_dimensions(arguments)

    # Get ligand list and number of ligands.
    ligand_list = natsorted( get_ligand_list(arguments['project'],
                                             arguments['protocol'],
                                             arguments['compounds']) )

    if arguments['overwrite'] : 
        prepared_list = []
        docked_list   = []
        prepare_list  = ligand_list
        dock_list     = ligand_list

    else:
        prepared_list = get_prepared_list(arguments['project'],
                                        arguments['protocol'],
                                        arguments['software'],
                                        ligand_list)


        docked_list = get_docked_list(arguments['project'],
                                    arguments['protocol'],
                                    arguments['software'],
                                    ligand_list)

        # By now I've read both prepared and docked lists
        # Make lists of what I need to resume.
        prepare_list = Diff(ligand_list,prepared_list)
        dock_list    = Diff(ligand_list,docked_list)



    arguments['nligands']=len(ligand_list)

    write_summary(arguments,
                   ligand_list,
                   prepared_list,
                   docked_list,
                   prepare_list,
                   dock_list)
    

    # Prepare receptor
    prepare_receptor(arguments['software'],
                     arguments['project'],
                     arguments['protocol'],
                     arguments['receptor'])


    # Write ligands to LigFlow originals folder (split mol2 file)
    split_mol2(arguments['project'],
               arguments['compounds'],
               arguments['nosplit'],
               arguments['nligands'])


    # Prepare ligands
    prepare_cmd_line=prepare_ligands(arguments['software'],
                                     arguments['project'],
                                     arguments['protocol'],
                                     prepare_list)

    docking_cmd_line=prepare_docking(arguments,
                                     dock_list)


    # Actually run calculations
    if len(prepare_cmd_line) > 0 :
        print('Preparing Ligands to Dock')
        run_commands(arguments['HPC'],arguments['njobs'],arguments['ncpus'],prepare_cmd_line,arguments['submit'])

    # Actually run calculations
    if not arguments['prepare'] : 
        if len(docking_cmd_line) > 0 :
            print('Docking !')
            run_commands(arguments['HPC'],arguments['njobs'],arguments['ncpus'],docking_cmd_line,arguments['submit'])


#####################################################################
# Functions                                                         #
#####################################################################
def write_hpc(first,last,cmd_line,ncpus,HPC) :

    if HPC == 'SGE' :
        header=f"""\
#!/bin/bash
#$ -N DFlow_{first}_{last}
#$ -S /bin/bash
#$ -q all.q@compute-*
#$ -pe orte {ncpus}
#$ -cwd
#$ -l s_rt=23:55:00
#$ -l h_rt=24:00:00
#$ -o DFlow_{first}_{last}.out
#$ -e DFlow_{first}_{last}.err
"""

    if HPC == 'SLURM' :
        header=f"""\
#!/bin/bash
#SBATCH -p public
#SBATCH --job-name=DFlow_{first}_{last}
#SBATCH -N 1
#SBATCH -n {ncpus}
#SBATCH -t 24:00:00
"""

    if HPC == 'PBS' :
        header=f"""\
#! /bin/bash
#PBS -q  route
#PBS -N DFlow_{first}_{last}
#PBS -l nodes=1:ppn={ncpus}
#PBS -l walltime=24:00:00
#PBS -V
"""

    xargs_cmd=f"""
cat <<EOF | xargs -P{ncpus} -I '{{}}' bash -c '{{}} >/dev/null'
"""

    with open('script.sge','w') as file:
        file.write(header)
        file.write(xargs_cmd)
    
        # Docking Loop
        for i in range(first,last) :
            file.write(cmd_line[i]+'\n')
        file.write('EOF')


def run_commands(HPC,njobs,ncpus,cmd_line,submit) :
    '''
    Run in parallel using python multiprocessing facility

    If HPC is enabled, user must provide the appropriate header for his/her HPC environment.

    '''

    if HPC :

        if HPC in ['SGE','PBS'] :
            submit_command='qsub'
        if HPC in ['SLURM'] :
            submit_command='sbatch'

        max_lines=len(cmd_line)

        for i in range(0,max_lines,njobs) :

            if i+njobs <= max_lines :
                    write_hpc(i,i+njobs,cmd_line,ncpus,HPC)
            else:
                    write_hpc(i,max_lines,cmd_line,ncpus,HPC)

            if submit :
                    job=subprocess.check_output([submit_command, 'script.sge']).decode('ascii')
                    with open('.job','w') as file:
                            file.write(job)
                
    else :
        import multiprocessing
        p = multiprocessing.Pool(ncpus)
        p.map(mp_worker, cmd_line)


def mp_worker(inputs):
    os.system(inputs)


def get_docked_list(project,protocol,software,ligand_list) :

    import shutil

    docked_list=[]

    if software in ['vina','qvina'] :
        ligand_name='out.pdbqt'

        for ligand in ligand_list :
            if os.path.isfile( os.path.join(project,'DockFlow',protocol,ligand,ligand_name) ) :
                docked_list.append(ligand)

    else :
        
        for ligand in ligand_list :

            path=os.path.join(project,'DockFlow',protocol,ligand,'dock')

            if os.path.isdir(path) :
                if os.path.isfile( os.path.join(path,'bestranking.csv') ):
                    if os.stat( os.path.join(path,'bestranking.csv')).st_size == 0 :
                        shutil.rmtree(path)
                    else:
                        docked_list.append(ligand)
                else :
                    shutil.rmtree(path)
        
    return docked_list


def get_prepared_list(project,protocol,software,ligand_list) :
    if software in ['vina','qvina'] :
        ligand_name='ligand.pdbqt'
    else :
        ligand_name='ligand.mol2'

    prepared_list=[]
    for ligand in ligand_list :
        if os.path.isfile( os.path.join(project,'DockFlow',protocol,ligand,ligand_name) ) :
            prepared_list.append(ligand)

    return prepared_list



def prepare_docking(arguments,ligand_list) :

    cmd_line=[]

    for ligand in ligand_list :

        out_dir = os.path.join(arguments['project'],'DockFlow',arguments['protocol'])

        if arguments['software'] in ['vina','qvina']  :

            write_vina_config(arguments,out_dir)

            if arguments['software'] == 'vina' :
                cmd_line.append('cd ' + os.path.join(out_dir,ligand) + ' ; '+ VINA_EXEC  + ' --config     ../config.in > /dev/null 2>&1' )

            elif arguments['software'] == 'qvina' :
                cmd_line.append('cd ' + os.path.join(out_dir,ligand) + ' ; '+ QVINA_EXEC  + ' --config    ../config.in > /dev/null 2>&1' )
 
        elif arguments['software'] == 'plants' :
            write_plants_config(arguments,out_dir)
            cmd_line.append('cd  ' + os.path.join(out_dir,ligand) + ' ; ' + PLANTS_EXEC + ' --mode screen ../config.in > /dev/null 2>&1')

    return cmd_line
    


def write_plants_config(arguments,out_dir) :
    with open (os.path.join(out_dir,'config.in'),'w') as f : 
        f.write(f'''
protein_file ../receptor.mol2
ligand_file  ligand.mol2

output_dir dock

scoring_function {arguments['scoring_function']}
search_speed     {arguments['speed']}
aco_ants         {arguments['ants']}
aco_evap         {arguments['evap_rate']}
aco_sigma        {arguments['iteration_scaling']}

bindingsite_center {arguments['center_x']} {arguments['center_y']} {arguments['center_z']}
bindingsite_radius {arguments['radius']}

write_multi_mol2 1

cluster_structures {arguments['num_modes']}
cluster_rmsd {arguments['cluster_rmsd']}

write_ranking_links 0
write_protein_bindingsite 0
write_protein_conformations 0
''')

def write_vina_config(arguments,out_dir) :
    with open (os.path.join(out_dir,'config.in'),'w') as f : 
        f.write(f'''
receptor       = ../receptor.pdbqt
ligand         = ligand.pdbqt
center_x       = {arguments['center_x']}
center_y       = {arguments['center_y']}
center_z       = {arguments['center_z']}
size_x         = {arguments['size_x']}
size_y         = {arguments['size_y']}
size_z         = {arguments['size_z']}
out            = out.pdbqt
log            = out.log
num_modes      = {arguments['num_modes']}
exhaustiveness = {arguments['exhaustiveness']}
energy_range   = {arguments['energy_range']}
cpu            = 1
''')


def prepare_ligands(software,project,protocol,ligand_list) :
    '''
    Create the output folder for each ligand
    Prepare the input .pdbqt or .mol2
    '''

    cmd_line=[]

    for ligand in ligand_list :
        
        out_dir     = os.path.join(project,'DockFlow',protocol,ligand)
        ligand_file = os.path.join(project,'LigFlow','originals',ligand+'.mol2')

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        if software in ['vina','qvina','smina'] :
            if not os.path.isfile( os.path.join ( out_dir,'ligand.pdbqt') ) :
                cmd=MGLTOOLS_BIN+'pythonsh ' + MGLTOOLS_UTIL+'prepare_ligand4.py' + ' -l ' + ligand_file +' -o '+out_dir+'/ligand.pdbqt  > /dev/null 2>&1'
                #os.system(cmd)            
                cmd_line.append(cmd)

        if software in ['plants'] :
            if not os.path.isfile( os.path.join ( out_dir,'ligand.mol2') ) :
                cmd=SPORES_EXEC+' --mode complete '+ligand_file+' '+out_dir+'/ligand.mol2 > /dev/null 2>&1 '
                #os.system(cmd)
                cmd_line.append(cmd)

    return cmd_line


def prepare_receptor(software,project,protocol,receptor) :
    '''
    Prepare docking will prepare the receptor structure for docking using the appropriate tool.

        prepare_receptor4.py from MGLTools if vina,qvina or smina are the docking software.
    
        SPORES_64bit if plants is the docking software.
    
    It will also create the command_line to prepare all ligands latter, where we'll decide to run
    using a HPC resource or locally.
    '''

    out_dir=os.path.join(project,'DockFlow',protocol)
    
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    if software in ['vina','qvina','smina'] :
        if not os.path.isfile( os.path.join( out_dir,'receptor.pdbqt' ) ) :
            print ('''
                   ############################################
                   # Preparing Receptor using "AutoDockTools" #
                   ############################################
            ''')
            cmd=MGLTOOLS_BIN+'pythonsh ' + MGLTOOLS_UTIL+'prepare_receptor4.py' + ' -r ' + receptor+' -o '+out_dir+'/receptor.pdbqt > /dev/null 2>&1'
            os.system(cmd)
            print(f'\nReceptor prepared at {out_dir}/receptor.pdbqt')


    if software in ['plants'] :
        if not os.path.isfile( os.path.join( out_dir,'receptor.mol2' )) :
            print ('''
                   ##################################### 
                   # Preparing Receptor using "SPORES" #
                   #####################################
            ''')
            cmd=SPORES_EXEC+' --mode settypes '+receptor+' '+out_dir+'/receptor.mol2 > /dev/null 2>&1'
            os.system(cmd)
            print(f'\nReceptor prepared at {out_dir}/receptor.mol2')

def write_summary (arguments,
                   ligand_list,
                   prepared_list,
                   docked_list,
                   prepare_list,
                   dock_list): 

    warning_message=''

    if arguments['overwrite'] :
        warning_message='(Overwriting)'

    if arguments['resume'] :
        warning_message='(Resuming)'


    print(f'''
#################################################
# DockFlow - Virtual Screening is great again ! #
#################################################

-------------------------------------------------
| ChemFlow stuff                                |
-------------------------------------------------
  Project : {arguments['project']} {warning_message}
 Protocol : {arguments['protocol']}''')

    if  arguments['blind'] :
        print(f'''
-------------------------------------------------
| Blind Docking requested (not implemented)     |
-------------------------------------------------
Center and Dimensions will be based on receptor + ligand sizes ''')

    print(f'''
-------------------------------------------------
| Docking parameters                            |
-------------------------------------------------
  Software : {arguments['software']} 
  Receptor : {arguments['receptor']}
 Compounds : {arguments['compounds']}
  Dockings : {arguments['nligands']}
 Remaining : {len(dock_list)}
 num_modes : {arguments['num_modes']}
    Center : {arguments['center_x']} {arguments['center_y']} {arguments['center_z']}''')

    if arguments['software'] == 'plants' :
        print(f'''    Radius : {arguments['radius']}''')
    else:
        print(f'''Dimensions : {arguments['size_x']} {arguments['size_y']} {arguments['size_z']}''')


    if  arguments['ref_ligand'] :
        print(f'''
-------------------------------------------------
| Template Docking                              |
-------------------------------------------------
reference ligand : {arguments['ref_ligand']}''')

    if arguments['HPC'] : 
        print(f'''
-------------------------------------------------
| High Performance Computing                    |
-------------------------------------------------
Scheduller : {arguments['HPC']}
ncores/job : {arguments['ncpus']}
njobs/host : {arguments['njobs']}
''')
    else :
        print(f'''
-------------------------------------------------
| Parallel Computing                            |
-------------------------------------------------
ncores : {arguments['ncpus']}''')

    if arguments['verbose'] :
        print(f'''
-------------------------------------------------
| Verbose mode:                                 |
-------------------------------------------------
Compounds:
{ligand_list}

Prepared:
{prepared_list}

Docked:
{docked_list}

Remaining to prepare:
{prepare_list}

Remaining to dock:
{dock_list}
''')
    print('''
Please cite us:
Diego E. B. Gomes, Cedric Bouysset, Marco Cecchini. Bioinformatics, 2020 
        ''')

def max_distance(points_axis, center_axis):
    dmax = 0
    for p in points_axis:
        d = abs(p - center_axis)
        if d > dmax:
            dmax = d
    return dmax

def binding_box(ref_ligand,padding):
    with open(ref_ligand,'r') as molecule :
        read_coordinates = False
        for line in molecule :
            if line.startswith('@<TRIPOS>BOND') :
                break
            if read_coordinates :
                c = line.split()
                x.append(float(c[2]))
                y.append(float(c[3]))
                z.append(float(c[4]))
                continue
            if line.startswith('@<TRIPOS>ATOM') :
                read_coordinates = True
                x = []
                y = []
                z = []

    if read_coordinates :
        n = len(x)
        cx=sum(x)/n
        cy=sum(y)/n
        cz=sum(z)/n
        if padding is None:
            padding = 0
        sx = (max_distance(x, cx) + padding)*2
        sy = (max_distance(y, cy) + padding)*2
        sz = (max_distance(z, cz) + padding)*2
        # sx = abs(max(x)-min(x)) + padding
        # sy = abs(max(y)-min(y)) + padding
        # sz = abs(max(z)-min(z)) + padding
        # print(f'Binding box dimensions for "{ligand}" :')
        # print(f'--center_x {cx:.3f} --center_y {cy:.3f} '\
        #       f'--center_z {cz:.3f} --size_x {sx:.3f} '\
        #       f'--size_y {sy:.3f} --size_z {sz:.3f}')
        return cx, cy, cz, sx, sy, sz
    else :
        print('Could not read coordinates!')
        quit()

def set_dimensions(arguments) :
    '''
    Set necessary dimensions
    '''
    
    software=arguments['software']

    # NOTE: if "blind" is active, dimensions must be recalculated on the fly

    if software in ['vina','qvina','smina'] :
        # Specific arguments for AutoDock Vina / Qvina / Smina
        size_x     = arguments['size_x']
        size_y     = arguments['size_y']
        size_z     = arguments['size_z']
        if not size_x or not size_y or not size_z:
            print('DockFlow.py: error: the following arguments are required: --size_x, --size_y and --size_z')
            quit()
    else :
        size_x = None
        size_y = None
        size_z = None

    if software in ['plants'] :
        # Specific arguments for PLANTS/GOLD
        radius     = arguments['radius']
        if not radius :
            print('DockFlow.py: error: the following arguments are required: --radius')
            quit()
    else : 
        radius = None

    return (size_x, size_y, size_z, radius)

    
def get_cmd_line():
    '''
    Need to be more flexible with the requirements.
        Vina needs "size_x,size_y,size_z"
       Plants only needs "radius".
    
    How to do it here ?

    '''
    parser = argparse.ArgumentParser(description = 'DockFlow.py VS - PLANTS only.')
    
    # General ChemFlow arguments
    required_args = parser.add_argument_group(description='Required arguments:')
    required_args.add_argument('-p','--project',
                        action   = 'store',
                        dest     = 'project',
                        required = True,
                        metavar='\b',
                        help     = 'Project name.')

    required_args.add_argument('-t','--protocol',
                        action   = 'store',
                        dest     = 'protocol',
                        default  = 'default',
                        required = True,
                        metavar='\b',
                        help     = 'Protocol name.')

    required_args.add_argument('-s','--software',
                        action   = 'store',
                        dest     = 'software',
                        required = True,
                        type     = str.lower,
                        choices  = ['vina','qvina','plants'],
                        metavar='\b',
                        help     = 'Docking software to use.')

    required_args.add_argument('-r','--receptor',
                        action   = 'store',
                        dest     = 'receptor',
                        required = True,
                        metavar='\b',
                        help     = 'Receptor filename.')

    required_args.add_argument('-c','--compounds',
                        action   = 'store',
                        dest     = 'compounds',
                        required = True,
                        metavar='\b',
                        help     = 'Compounds file name (mol2).')

    # Commom docking arguments
    software_options = parser.add_argument_group(description='Common docking parameters:')
    software_options.add_argument('-x','--center_x',
                        action   = 'store',
                        dest     = 'center_x',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Center X')

    software_options.add_argument('-y','--center_y',
                        action   = 'store',
                        dest     = 'center_y',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Center Y')

    software_options.add_argument('-z','--center_z',
                        action   = 'store',
                        dest     = 'center_z',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Center Z')

    software_subparser = parser.add_subparsers(dest='run_vina, run_plants',required=True,
                                               help='Must be the last provided arguments.')
    # Vina,Qvina,Smina specific options.
    vina_parser = software_subparser.add_parser('run_vina', help='Arguments for Vina, Qvina, Smina. Help: run_vina -h, --help')
    vina_parser.add_argument('-sx','--size_x',
                        action   = 'store',
                        dest     = 'size_x',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Size X')

    vina_parser.add_argument('-sy','--size_y',
                        action   = 'store',
                        dest     = 'size_y',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Size Y')

    vina_parser.add_argument('-sz','--size_z',
                        action   = 'store',
                        dest     = 'size_z',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Size Z')

    vina_parser.add_argument('--ref_ligand',
                        action   = 'store',
                        dest     = 'ref_ligand',
                        required = False,
                        metavar='\b',
                        help     = 'Automaticaly calculates the binding box (Center X, Center Y, Center Z, '\
                                   'Size X, Size Y and Size Z) for Vina based on the ligand. It uses '\
                                   'the provided argument (mol2) as reference ligand.')

    vina_parser.add_argument('--padding',
                        action   = 'store',
                        dest     = 'padding',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Extra space for the binding box.')

    vina_parser.add_argument('-ex','--exhaustiveness',
                        action   = 'store',
                        dest     = 'exhaustiveness',
                        default  = '8',
                        type     = int,
                        required = False, 
                        metavar='\b',
                        help     = 'Exhaustiveness.')

    vina_parser.add_argument('-er','--energy-range',
                        action   = 'store',
                        dest     = 'energy_range',
                        default  = '3',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Energy range between the best and worst result in kcal/mol.')

    # Specific for PLANTS
    plants_parser = software_subparser.add_parser('run_plants', help='Arguments for PLANTS. Help: run_plants -h, --help')
    plants_parser.add_argument('--radius',
                        action   = 'store',
                        dest     = 'radius',
                        required = False,
                        type     = float,
                        metavar='\b',
                        help     = 'Sphere radius.')

    plants_parser.add_argument('--sf',
                        action   = 'store',
                        dest     = 'scoring_function',
                        required = False,
                        type     = str.lower,
                        default  = 'chemplp',
                        choices  = ['chemplp','plp','plp95'],
                        metavar='\b',
                        help     = 'Scoring function.')

    plants_parser.add_argument('--speed',
                        action   = 'store',
                        dest     = 'speed',
                        required = False,
                        type     = str.lower,
                        default  = 'speed1',
                        choices  = ['speed1','speed2','speed3'],
                        metavar='\b',
                        help     = 'Search speed.'\
                                   'speed1 slow, accurate'\
                                   'speed4: fast, low acuracy')
    plants_parser.add_argument('--ants',
                        action   = 'store',
                        dest     = 'ants',                        
                        default  = '20',
                        type     = int,
                        required = False,
                        metavar='\b',
                        help     = 'Number of ants.')

    plants_parser.add_argument('--evap-rate',
                        action   = 'store',
                        dest     = 'evap_rate',                        
                        default  = '0.15',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Evaporation rate.')

    plants_parser.add_argument('--iteration-scaling',
                        action   = 'store',
                        dest     = 'iteration_scaling',                        
                        default  = '1.0',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Iteration scaling.')

    plants_parser.add_argument('--cluster-rmsd',
                        action   = 'store',
                        dest     = 'cluster_rmsd',                        
                        default  = '2.0',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'RMSD to Cluster docking poses.')

    special_parser = parser.add_argument_group(description='Special docking arguments:')
    special_parser.add_argument('--num_modes',
                        action = 'store',
                        dest = 'num_modes',
                        default='10',
                        type     = int,
                        required = False,
                        metavar='\b',
                        help = 'Number of docking poses.')

    special_parser.add_argument('--ligand',
                        action = 'store',
                        dest = 'ref_ligand',
                        required = False,
                        metavar='\b',
                        help = 'Reference ligand file name (mol2) for template-based docking (PLANTS only).')

    special_parser.add_argument('--blind' ,
                        action = 'store_true',
                        dest = 'blind',
                        required = False,
                        help = 'Enable blind docking to receptor.')

    hpc_parser = parser.add_argument_group(description='High Performance Computing options:')
    hpc_parser.add_argument('--hpc',
                        action = 'store',
                        dest = 'HPC',
                        required = False,
                        type = str.upper,
                        choices = ['SGE', 'PBC', 'SLURM'],
                        metavar='\b',
                        help = 'Choose among the supported schedulers.')

    hpc_parser.add_argument('--template',
                        action = 'store',
                        dest = 'template',
                        required = False,
                        metavar='\b',
                        help = 'A text-file template containing any special options for your HPC environment '\
                        'To see more examples, type: DockFlow.py --show-templates.')

    hpc_parser.add_argument('--submit',
                        action = 'store_true',
                        dest = 'submit',
                        required = False,
                        help = 'Submit to queue.')
 
    hpc_parser.add_argument('--njobs',
                        action = 'store',
                        dest = 'njobs',
                        default='64',
                        type     = int,
                        required = False,
                        metavar='\b',
                        help = 'Number of ligands per HPC job [64].')

    hpc_parser.add_argument('--ncpus',
                        action = 'store',
                        dest = 'ncpus',
                        default='8',
                        type = int,
                        required = False,
                        metavar='\b',
                        help = 'Number of processors to user per HPC/local job [8].')

    # If you just need to prepare the systems or just run the workflow
    other = parser.add_argument_group(description='Other options:')
    other.add_argument('-o', '--overwrite',
                       action='store_true',
                       dest='overwrite',
                       required=False,
                       help='Overwrite dockings.')

    other.add_argument('-v', '--verbose',
                       action='store_true',
                       dest='verbose',
                       help='Verbose mode.')

    other.add_argument('--resume',
                       action='store_true',
                       dest='resume',
                       required=False,
                       help='When resuming, disable split_mol2.')

    other.add_argument('--prepare',
                       action='store_true',
                       dest='prepare',
                       required=False,
                       help='Prepare ligands, instead of docking.')

    # Kind of useless to re-split, i'd better test first if compounds are there and user overwrite instead
    other.add_argument('--nosplit',
                       action='store_true',
                       dest='nosplit',
                       required=False,
                       help='Do not split mol2 (already splitted).')

    arg_dict = vars(parser.parse_args())
    # print(arg_dict)

    return arg_dict


if __name__ == "__main__":
    main()
