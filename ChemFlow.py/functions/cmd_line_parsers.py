def dockflow_parser():
    '''
    Need to be more flexible with the requirements.
        Vina needs "size_x,size_y,size_z"
       Plants only needs "radius".
    
    How to do it here ?

    '''
    import argparse

    parser = argparse.ArgumentParser(description = '''### DockFlow ###''')
    
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

    required_args.add_argument('-r','--receptor',
                        action   = 'store',
                        dest     = 'receptor',
                        required = True,
                        metavar='\b',
                        help     = 'Receptor filename.')

    required_args.add_argument('-l','--ligand',
                        action   = 'store',
                        dest     = 'compounds',
                        required = True,
                        metavar='\b',
                        help     = 'Ligand(s) file name (mol2).')

    # If you just need to prepare the systems or just run the workflow
    other = parser.add_argument_group(description='Other options:')
    other.add_argument('-o', '--overwrite',
                       action    = 'store_true',
                       dest      = 'overwrite',
                       help      = 'Overwrite outputs.')

    other.add_argument('-v', '--verbose',
                       action    = 'store_true',
                       dest      = 'verbose',
                       help      = 'Verbose mode.')


    # Mutually exclusive group
    docking_required = parser.add_mutually_exclusive_group(required=True)
    docking_required.add_argument('-c','--center',
                        action   = 'store',
                        dest     = 'center',
                        type     = float,
                        nargs    = 3,
                        metavar='\b',
                        help     = 'XYZ center for docking. 3 argumens')

    docking_required.add_argument('--ref','--referece',
                        action   = 'store',
                        dest     = 'reference',
                        metavar='\b',
                        help     = 'Reference ligand file name (mol2). Used for automatically setting docking Center and Size/Radius.')

    docking_optional = parser.add_argument_group(description='Special docking arguments:')
    docking_optional.add_argument('--padding',
                        action   = 'store',
                        dest     = 'padding',
                        type     = float,
                        required = False,
                        metavar='\b',
                        help     = 'Extra space for the binding box.')

    docking_optional.add_argument('--num_modes',
                        action   = 'store',
                        dest     = 'num_modes',
                        default  = 10,
                        type     = int,
                        required = False,
                        metavar  = '\b',
                        help     = 'Number of docking poses.')

    docking_optional.add_argument('--blind' ,
                        action   = 'store_true',
                        dest     = 'blind',
                        required = False,
                        help     = 'Enable blind docking to receptor.')

    
    # Create parser for software.
    software_subparser = parser.add_subparsers(dest='software',
                                               required=True,
                                               title='Software to run')

    plants_parser = software_subparser.add_parser('plants')
    vina_parser   = software_subparser.add_parser('vina')
    qvina_parser  = software_subparser.add_parser('qvina')
    smina_parser  = software_subparser.add_parser('smina')    

    # Vina,Qvina,Smina Share some specific options.
    for subparser in [vina_parser, qvina_parser,smina_parser]:
        subparser.add_argument('--size',
                        action   = 'store',
                        dest     = 'size',
                        type     = float,
                        required = False,
                        default  = [15.0,15.0,15.0],
                        nargs    = 3,
                        metavar='\b',
                        help     = 'Grid Size (Space-separated argumens for X Y Z')
        subparser.add_argument('--exhaustiveness',
                        action   = 'store',
                        dest     = 'exhaustiveness',
                        type     = int,
                        required = False,
                        default  = 8,
                        metavar='\b',
                        help     = 'Search Exhaustiveness')
        subparser.add_argument('--energy-range',
                        action   = 'store',
                        dest     = 'energy_range',
                        type     = float,
                        required = False,
                        default  = 3.0,
                        metavar='\b',
                        help     = 'Energy range [3 kcal/mol]')


    # Specific for PLANTS
    plants_parser.add_argument('--radius',
                        action   = 'store',
                        dest     = 'radius',
                        required = True,
                        type     = float,
                        metavar='\b',
                        help     = 'Sphere radius.')

    plants_parser.add_argument('--scoring-function',
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
                        metavar='',
                        help     = 'RMSD to Cluster docking poses.')

#####################################################################
# Runtime options

    hpc_parser = parser.add_argument_group(description='High Performance Computing options:')
    hpc_parser.add_argument('--hpc',
                        action   = 'store',
                        dest     = 'HPC',
                        required = False,
                        type     = str.upper,
                        choices  = ['SGE', 'PBC', 'SLURM'],
                        metavar  = '',
                        help     = 'Choose among the supported schedulers.')

    hpc_parser.add_argument('--template',
                        action   = 'store',
                        dest     = 'template',
                        required = False,
                        metavar  = '',
                        help     = 'A text-file template containing any special options for your HPC environment '\
                        'To see more examples, type: DockFlow.py --show-templates.')

    hpc_parser.add_argument('--submit',
                        action   = 'store_true',
                        dest     = 'submit',
                        required = False,
                        help     = 'Submit to queue.')
 
    hpc_parser.add_argument('--njobs',
                        action   = 'store',
                        dest     = 'njobs',
                        default  = '64',
                        type     = int,
                        required = False,
                        metavar  = '',
                        help     = 'Number of ligands per HPC job [64].')

    hpc_parser.add_argument('--ncpus',
                        action   = 'store',
                        dest     = 'ncpus',
                        default  = '8',
                        type     = int,
                        required = False,
                        metavar  = '',
                        help     = 'Number of processors to user per HPC/local job [8].')



    arg_dict = vars(parser.parse_args())

    # Update General ChemFlow arguments
    try :
        arg_dict['project'] = arg_dict['project'].split('.chemflow')[0]
    except :
        pass
    arg_dict['project']=arg_dict['project']+'.chemflow'

    return arg_dict


if __name__ == "__main__":
    main()
