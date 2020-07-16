def dockflow_summary (arguments,
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
