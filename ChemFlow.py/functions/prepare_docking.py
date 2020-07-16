def write_plants_config(arguments,out_dir) :
    import os
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

bindingsite_center {arguments['center'][0]} {arguments['center'][1]} {arguments['center'][2]}
bindingsite_radius {arguments['radius']}

write_multi_mol2 1

cluster_structures {arguments['num_modes']}
cluster_rmsd {arguments['cluster_rmsd']}

write_ranking_links 0
write_protein_bindingsite 0
write_protein_conformations 0
''')

def write_vina_config(arguments,out_dir) :
    import os

    with open (os.path.join(out_dir,'config.in'),'w') as f : 
        f.write(f'''
receptor       = ../receptor.pdbqt
ligand         = ligand.pdbqt
center_x       = {arguments['center'][0]}
center_y       = {arguments['center'][1]}
center_z       = {arguments['center'][2]}
size_x         = {arguments['size'][0]}
size_y         = {arguments['size'][1]}
size_z         = {arguments['size'][2]}
out            = out.pdbqt
log            = out.log
num_modes      = {arguments['num_modes']}
exhaustiveness = {arguments['exhaustiveness']}
energy_range   = {arguments['energy_range']}
cpu            = 1
''')


def prepare_receptor(arguments) :
    '''
    Prepare docking will prepare the receptor structure for docking using the appropriate tool.

        prepare_receptor4.py from MGLTools if vina,qvina or smina are the docking software.
    
        SPORES_64bit if plants is the docking software.
    
    It will also create the command_line to prepare all ligands latter, where we'll decide to run
    using a HPC resource or locally.
    '''
    import os
    import subprocess
    
    MGLTOOLS_BIN  = os.getenv('CONDA_PREFIX')+'/bin/'
    SPORES_EXEC   = os.getenv('SPORES_EXEC')

    out_dir=os.path.join(arguments['project'],'DockFlow',arguments['protocol'])
    
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    if arguments['software'] in ['vina','qvina','smina'] :
        if not os.path.isfile( os.path.join( out_dir,'receptor.pdbqt' ) ) :
            print ('''
                   ############################################
                   # Preparing Receptor using "AutoDockTools" #
                   ############################################
            ''')
            cmd=['python2',os.path.join(MGLTOOLS_BIN,'prepare_receptor4.py'),'-r',arguments['receptor'],'-o',out_dir+'/receptor.pdbqt']

            with open(os.path.join(out_dir,"prepare_receptor.log"), "w") as file:
                try : 
                    subprocess.run(cmd, stdout=file,stderr=subprocess.DEVNULL)
                except :
                    print(f'''Prepare receptor failed, check log at {os.path.join(out_dir,"prepare_receptor.log")}''')
                    quit()

            print(f'\nReceptor prepared at {out_dir}/receptor.pdbqt')


    if arguments['software'] in ['plants'] :
        if not os.path.isfile( os.path.join( out_dir,'receptor.mol2' )) :
            print ('''
                   ##################################### 
                   # Preparing Receptor using "SPORES" #
                   #####################################
            ''')
            cmd = [SPORES_EXEC,'--mode','settypes',arguments['receptor'],os.path.join(out_dir,'receptor.mol2')]

            with open(os.path.join(out_dir,"prepare_receptor.log"), "w") as file:
                try : 
                    subprocess.run(cmd, stdout=file,stderr=subprocess.DEVNULL)
                except :
                    print(f'''Prepare receptor failed, check log at {os.path.join(out_dir,"prepare_receptor.log")}''')
                    quit()

            print(f'\nReceptor prepared at {out_dir}/receptor.mol2')
