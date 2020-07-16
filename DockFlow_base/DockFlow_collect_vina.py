#!/usr/bin/env python
# coding: utf-8
# Config

############################################################
# Imports                                                  #
############################################################
import sys
import os
import argparse
import pickle
import time

############################################################
# Functions                                                #
############################################################
def main():
    """
	Main Function
    """

    # Timing
    main_time = time.process_time()

    ##    write_header()

    # Get the command line arguments
    arguments = get_cmd_line()

    # Check if output exists
    if os.path.isfile(arguments['output_file']) and not arguments['overwrite']:
        arguments['overwrite'] = prevent_overwrite(arguments['output_file'])

    # Set the path to ChemFlow project
    path = os.path.join(arguments['project'], 'DockFlow', arguments['protocol'])

    # List subfolders at the path
    ligand_list = get_ligand_list_from_project(arguments['project'],
                                               arguments['protocol'])

    # Store number of ligands
    nligands = len(ligand_list)

    # Get all energies
    ncores = arguments['ncores']
    if ncores is None:
        ncores = 1
    if ncores == 1:
        output = get_energies(path, ligand_list, arguments['readline'])
    else:
        output = parallel_get_energies(path, ligand_list, ncores, arguments['readline'])
    
    # Write output file
    write_output(output, arguments['output_file'])
    
    # Timing
    main_time = time.process_time() - main_time
    minutes, seconds = divmod(main_time, 60)
    hours, minutes = divmod(int(minutes), 60)
    print(f'''Elapsed time: {hours:02d}h:{minutes:02d}m:{seconds:04.2f}s''')


def get_ligand_list_from_project(project, protocol):
    '''
    Extract ligand list from .pickle file, or look aftr files to list it
    '''
    ligand_list = []
    try:
        if os.path.isfile(project + '/LigFlow/.ligands'):
            with open(project + '/LigFlow/.ligands', 'rb') as f:
                ligand_list = pickle.load(f)

        else:
            for ligand in next(os.walk(project + '/LigFlow/originals/'))[2]:
                ligand_list.append(ligand.split('.')[0])
            with open(project + '/LigFlow/.ligands', 'wb') as f:
                pickle.dump(ligand_list, f)

    except Exception as e:
        print(str(e))
        print('[Error] Could not get ligand list')
        quit()

    return ligand_list


def parallel_get_energies(path, ligand_list, ncores, readline):
    from functools import partial
    from multiprocessing import Pool
    from tqdm import tqdm
    import itertools

    length = len(ligand_list)
    workers = min(ncores, length)
    with Pool(workers) as pool:
        if not readline:
            results = tuple(tqdm(pool.imap(partial(get_energy_whole_file, path=path), ligand_list), total=length, unit=' files'))
        else:
            results = tuple(tqdm(pool.imap(partial(get_energy, path=path), ligand_list), total=length, unit=' files'))

    # merge results
    return list(itertools.chain.from_iterable(results))


def get_energies(path, ligand_list, readline):
    # from progress.bar import Bar
    from tqdm import tqdm

    '''
    Notice here I have to EXTEND instead of APPEND the list
    https://www.geeksforgeeks.org/append-extend-python/
    '''

    # bar = Bar('Getting Energies :', max=len(ligand_list))

    # Initialize the output list.
    output = []

    # Get energies   
    for ligand in tqdm(ligand_list, total=len(ligand_list), unit=' files'):
    # for ligand in ligand_list:
        filename = os.path.join(path, ligand, 'out.log')

        if os.path.isfile(filename):
            if not readline:
                output.extend(get_energy_whole_file(ligand, path))
            else:
                output.extend(get_energy(ligand, path))
        # bar.next()

    # bar.finish()

    return output


def get_energy(ligand, path):
    '''
    Read an autodock Vina/Smina/Qvina .log output file
    '''
    filename = os.path.join(path, ligand, 'out.log')
    pose=0
    energy_list=[]

    with open(filename, 'r') as f:
        # Read line by line
        for line in f :
            if pose > 0 :
                energy = line.split()[1]
                if energy != 'output':
                    energy_list.append([ligand, str(pose), energy])
                    pose += 1
            elif line.startswith("-----"):
                pose=1

    return energy_list

def get_energy_whole_file(ligand, path):
    '''
    Read an autodock Vina/Smina/Qvina .log output file
    '''
    filename = os.path.join(path, ligand, 'out.log')
    pose=0
    energy_list=[]

    with open(filename, 'r') as f:
        # Read the whole file
        filecontent = f.readlines()
        for line in filecontent :
            if pose > 0 :
                energy = line.split()[1]
                if energy != 'output':
                    energy_list.append([ligand, str(pose), energy])
                    pose += 1
            elif line.startswith("-----"):
                pose=1

    return energy_list


def write_output(output, output_file):
    # Write output
    with open(output_file, 'w') as f:
        f.write('id,pose,vina_score\n')

        for i in output:
            f.write(i[0] + ',' + i[1] + ',' + i[2] + '\n')


def prevent_overwrite(output_file):
    yes = {'yes', 'y', 'ye', ''}
    no = {'no', 'n'}

    print(f'Warning: {output_file} already exists')
    choice = input('Overwrite: Y/n? ').lower()

    if choice in yes:
        return True

    elif choice in no:
        sys.exit('Nothing done here. "Au revoir"')

    else:
        print("Please respond with 'yes' or 'no'")
        prevent_overwrite(output_file)


def get_cmd_line():
    parser = argparse.ArgumentParser(description='Collect Autodock Vina results')

    parser.add_argument('--project',
                        action='store',
                        dest='project',
                        required=True,
                        help='Project name.')

    parser.add_argument('--protocol',
                        action='store',
                        dest='protocol',
                        default='default',
                        required=False,
                        help='Protocol name.')

    parser.add_argument('--compounds',
                        action='store',
                        dest='compounds',
                        default='default',
                        required=False,
                        help='Compound .mol2 (only for those in this file')

    parser.add_argument('--out',
                        action='store',
                        dest='output_file',
                        default='DockFlow_vina.csv',
                        required=False,
                        help='Output file name [DockFlow_vina.csv]')

    parser.add_argument('--overwrite',
                        action='store_true',
                        dest='overwrite',
                        required=False,
                        help='Overwrite output file')

    
    parser.add_argument('--ncores',
                        action='store',
                        dest='ncores',
                        default=int(os.cpu_count()/2),
                        required=False,
                        help='Number of processors [default: max/2]')

    parser.add_argument('--readline',
                        action='store_true',
                        dest='readline',
                        required=False,
                        help='Read file line by line')

    arg_dict = vars(parser.parse_args())
    try:
        arg_dict['ncores'] = int(arg_dict['ncores'])
    except:
        arg_dict['ncores'] = 1

    try:
        arg_dict['project'] = arg_dict['project'].split('.chemflow')[0]
    except:
        pass

    # Update dictionary
    arg_dict['project'] = arg_dict['project'] + '.chemflow'

    return arg_dict


if __name__ == "__main__":
    main()
