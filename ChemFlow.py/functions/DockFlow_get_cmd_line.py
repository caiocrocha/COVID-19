def get_cmd_line():
    '''
    Need to be more flexible with the requirements.
        Vina needs "size_x,size_y,size_z"
       Plants only needs "radius".
    
    How to do it here ?

    '''
    import argparse
    
    parser = argparse.ArgumentParser(description = 'DockFlow.py VS - PLANTS only.')
    
    # General ChemFlow arguments
    parser.add_argument('-p','--project',
                        action   = 'store',
                        dest     = 'project',
                        required = True,
                        metavar=None,
                        help     = 'Project name.')

    parser.add_argument('-t','--protocol',
                        action   = 'store',
                        dest     = 'protocol',
                        default  = 'default',
                        required = False,
                        metavar='\b',                        
                        help     = 'Protocol name.')

    parser.add_argument('-o','--overwrite',
                        action   = 'store_true',
                        dest     = 'overwrite',
                        required = False,
                        help     = 'Overwrite dockings.')

    parser.add_argument('-v','--verbose',
                        action   = 'store_true',
                        dest     = 'verbose',
                        help     = 'Number of processors to user per HPC/local job [8]')                        

    parser.add_argument('-d','--debug',
                        action = 'store_true',
                        dest = 'debug',
                        help = 'Debug mode')

    # If you just need to prepare the systems or just run the workflow                   
    parser.add_argument('--resume',
                        action   = 'store_true',
                        dest     = 'resume',
                        required = False,
                        help     = 'When resuming, disable split_mol2.')

    parser.add_argument('--prepare',
                        action   = 'store_true',
                        dest     = 'prepare',
                        required = False,
                        help     = 'Prepare ligands, instead of docking.')

    # Kind of useless to re-split, i'd better test first if compounds are there and user overwrite instead
    parser.add_argument('--nosplit',
                        action   = 'store_true',
                        dest     = 'nosplit',
                        required = False,
                        help     = 'Do not split .mol2 (already splitted)')

    # Commom docking arguments
    parser.add_argument('--software',
                        action   = 'store',
                        dest     = 'software',
                        required = True,
                        choices  = ['vina','qvina','plants'],
                        metavar='\b',
                        help     = 'Docking software to use')

    parser.add_argument('-r','--receptor',
                        action   = 'store',
                        dest     = 'receptor',
                        required = True,
                        metavar='\b',
                        help     = 'Receptor filename.')

    parser.add_argument('-c','--compounds',
                        action   = 'store',
                        dest     = 'compounds',
                        required = True,
                        metavar='\b',
                        help     = 'Compounds file name (mol2).')

    parser.add_argument('-x','--center_x',
                        action   = 'store',
                        dest     = 'center_x',
                        type     = float,
                        required = True,
                        metavar='\b',
                        help     = 'Center X')

    parser.add_argument('-y','--center_y',
                        action   = 'store',
                        dest     = 'center_y',
                        type     = float,
                        required = True,
                        metavar='\b',
                        help     = 'Center Y')

    parser.add_argument('-z','--center_z',
                        action   = 'store',
                        dest     = 'center_z',
                        type     = float,
                        required = True,
                        metavar='\b',
                        help     = 'Center Z')
    
    # Vina,Qvina,Smina specific options.
    parser.add_argument('-sx','--size_x',
                        action   = 'store',
                        dest     = 'size_x',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Size X')

    parser.add_argument('-sy','--size_y',
                        action   = 'store',
                        dest     = 'size_y',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Size Y')

    parser.add_argument('-sz','--size_z',
                        action   = 'store',
                        dest     = 'size_z',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Size Z')

    parser.add_argument('-ex','--exhaustiveness',
                        action   = 'store',
                        dest     = 'exhaustiveness',
                        default  = '8',
                        type     = int,
                        required = False, 
                        metavar='\b',
                        help     = 'Exhaustiveness')

    parser.add_argument('-er','--energy-range',
                        action   = 'store',
                        dest     = 'energy_range',
                        default  = '3',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Energy range between the best and worst result in kcal/mol')

    # Specific for PLANTS
    parser.add_argument('--radius',
                        action   = 'store',
                        dest     = 'radius',
                        required = False,
                        type     = float,
                        metavar='\b',
                        help     = 'Sphere radius')

    parser.add_argument('--sf',
                        action   = 'store',
                        dest     = 'scoring_function',
                        required = False,
                        default  = 'chemplp',
                        choices  = ['chemplp','plp','plp95'],
                        metavar='\b',
                        help     = 'Scoring function')

    parser.add_argument('--speed',
                        action   = 'store',
                        dest     = 'speed',
                        required = False,
                        default  = 'speed1',
                        choices  = ['speed1','speed2','speed3'],
                        metavar='\b',
                        help     = 'Search speed.'\
                                   'speed1 slow, accurate'\
                                   'speed4: fast, low acuracy')
    parser.add_argument('--ants',
                        action   = 'store',
                        dest     = 'ants',                        
                        default  = '20',
                        type     = int,
                        required = False,
                        metavar='\b',
                        help     = 'Number of ants')

    parser.add_argument('--evap-rate',
                        action   = 'store',
                        dest     = 'evap_rate',                        
                        default  = '0.15',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Evaporation rate')

    parser.add_argument('--iteration-scaling',
                        action   = 'store',
                        dest     = 'iteration_scaling',                        
                        default  = '1.0',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Iteration scaling')

    parser.add_argument('--cluster-rmsd',
                        action   = 'store',
                        dest     = 'cluster_rmsd',                        
                        default  = '2.0',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'RMSD to Cluster docking poses')

    # Special docking arguments
    parser.add_argument('--num_modes',
                        action = 'store',
                        dest = 'num_modes',
                        default='10',
                        type     = int,
                        required = False,
                        metavar='\b',
                        help = 'Number of docking poses')

    parser.add_argument('--ligand',
                        action = 'store',
                        dest = 'ref_ligand',
                        required = False,
                        metavar='\b',
                        help = 'Reference ligand file name (mol2) for template-based dockint (PLANTS only)')

    parser.add_argument('--blind' ,
                        action = 'store_true',
                        dest = 'blind',
                        required = False,
                        help = 'Enable blind docking to receptor.')

    # High Performance Computing options.
    parser.add_argument('--hpc',
                        action = 'store',
                        dest = 'HPC',
                        required = False,
                        choices = ['SGE', 'PBC', 'SLURM'],
                        metavar='\b',
                        help = 'Choose among the supported schedulers')

    parser.add_argument('--template',
                        action = 'store',
                        dest = 'template',
                        required = False,
                        metavar='\b',
                        help = 'A text-file template containing any special options for your HPC environment '\
                        'To see more examples, type: DockFlow.py --show-templates')

    parser.add_argument('--submit',
                        action = 'store_true',
                        dest = 'submit',
                        required = False,
                        help = 'Submit to queue')
 
    parser.add_argument('--njobs',
                        action = 'store',
                        dest = 'njobs',
                        default='64',
                        type     = int,
                        required = False,
                        metavar='\b',
                        help = 'Number of ligands per HPC job. [64]')

    parser.add_argument('--ncpus',
                        action = 'store',
                        dest = 'ncpus',
                        default='8',
                        type = int,
                        required = False,
                        metavar='\b',
                        help = 'Number of processors to user per HPC/local job [8]')

    arguments = vars(parser.parse_args())


    # Update General ChemFlow arguments
    try :
        arguments['project'] = arguments['project'].split('.chemflow')[0]
    except :
        pass
    arguments['project']=arguments['project']+'.chemflow'


    return arguments
