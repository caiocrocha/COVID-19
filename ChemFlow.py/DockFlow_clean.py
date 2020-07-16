#!/usr/bin/env python3
# coding: utf-8
# Config

def main () :
    import os
    from functions.cmd_line_parsers import dockflow_parser
    from functions.write_summary    import dockflow_summary
#    from functions.set_dimensions   import set_dimensions

    arguments = dockflow_parser()

# Create project folder
#--------------------------------------------------------------------
    rundir = os.path.join(arguments['project'],'DockFlow',arguments['protocol'])
    if not os.path.isdir(rundir) : 
        os.makedirs(rundir)

# Generate/Read ligand list (.pickle file) 
#--------------------------------------------------------------------
    from functions.mol2_index import get_indexes    
    
    index_list  = get_indexes(arguments)            # Dictionary with ligands 
                                                    # and their 1st byte position int the mol2 file.
    
    ligand_list = index_list.keys()                 # Dictionary keys, containing ligand names.
    arguments['nligands'] = len(ligand_list)        # New entry to store number of ligands


# Checkpoint step.
#--------------------------------------------------------------------
    from functions.mol2_index import get_docked_list
    dock_list = get_docked_list(arguments,ligand_list)
    arguments['ndock'] = len(dock_list)


# Prepare receptor
#--------------------------------------------------------------------
    from functions.prepare_docking import prepare_receptor
    prepare_receptor(arguments)


# Write docking config file
#--------------------------------------------------------------------
    from functions.prepare_docking import write_vina_config,write_plants_config
    out_dir=os.path.join(arguments['project'],'DockFlow',arguments['protocol'])

    if arguments['software'] in ['vina','qvina','smina'] :
        write_vina_config(arguments,out_dir)

    if arguments['software'] == 'plants' :
        write_plants_config(arguments,out_dir)

# Run
#--------------------------------------------------------------------
    from functions.run_docking import run_dockflow
    if len(dock_list) > 0 :
        run_dockflow(arguments,index_list,dock_list)



    print(f'''
   Project : {arguments['project']}
  Protocol : {arguments['protocol']}
  Software : {arguments['software']} 
  Receptor : {arguments['receptor']}
 Compounds : {arguments['compounds']}
   Ligands : {arguments['nligands']}
  Dockings : {arguments['ndock']}
 num_modes : {arguments['num_modes']}
    Center : {arguments['center'][0]} {arguments['center'][1]} {arguments['center'][2]}

''')

  

def write_summary(arguments) :


    print(f'''
#################################################
# DockFlow - Virtual Screening is great again ! #
#################################################

-------------------------------------------------
| ChemFlow stuff                                |
-------------------------------------------------
  Project : {arguments['project']}
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
reference ligand : {ref_ligand}''')

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



if __name__ == "__main__":
    main()
