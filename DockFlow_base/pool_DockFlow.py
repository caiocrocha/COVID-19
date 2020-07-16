#!/usr/bin/env python3
# coding: utf-8
# Config

import os
import subprocess
import argparse
import multiprocessing.pool
import functools

def get_cmd_line():
    parser = argparse.ArgumentParser(description='Run DockFlow in parallel')
    parser.add_argument('-b', '--basedir', action='store', dest='basedir', required=False, metavar='/path/to/ChemFlow/home', help='ChemFlow base directory')
    parser.add_argument('-t', '--targetdir', action='store', dest='targetdir', required=False, help='Target directory containing subdirectories with files for docking')
    parser.add_argument('-s', '--software', action='store', dest='software', required=False, metavar='vina', help='Docking software')
    parser.add_argument('-p', '--protocol', action='store', dest='protocol', required=False, help='Directory name for the directory containing the results')
    parser.add_argument('-P', '--processors', action='store', dest='processors', required=False, default=os.cpu_count(), help='Default: max number of CPU cores detected')
    parser.add_argument('-a', '--additional', action='store', dest='additional', required=False, nargs='*', metavar='ex 32 er 3', help='String containing additional arguments for DockFlow')
    arg_dict = vars(parser.parse_args())
    return arg_dict

def _directory_worker(basedir, targetdir, software, protocol, padding, additionalFormated, subdir):
    coordinates = subprocess.run(f'{basedir}/binding_box.py '\
            f'{targetdir}/{subdir}/{subdir}_ligand.mol2 --padding {padding}', 
            stdout=subprocess.PIPE, shell=True).stdout.decode('ascii').strip()
    subprocess.run(f'{basedir}/DockFlow.py \
        -p {targetdir} \
        --protocol {subdir}_{software}_{protocol} \
        --software {software} \
        -r {targetdir}/{subdir}/{subdir}_protein.pdb \
        -c {targetdir}/{subdir}/{subdir}_ligand.mol2 \
        {coordinates} \
        {additionalFormated}', shell=True)

def directory_processor(basedir, targetdir, software, protocol, processors, padding, additional):
    if processors is None:
        processors = 1
        print("Could not detect number of CPU cores. Only 1 processor will be used.")
    if additional is not None:
        additionalFormated = ' '.join(f'-{additional[i]} {additional[i+1]}' for i in range(0, len(additional), 2))
    else:
        additionalFormated = ''

    subdirs = [subdir for subdir in os.listdir(targetdir)]
    lendir = len(subdirs)
    # pick number of workers....
    worker_count = min(processors, lendir)
    with multiprocessing.Pool(worker_count) as pool:
        pool.map(functools.partial(_directory_worker, 
            basedir, targetdir, software, protocol,
            padding, additionalFormated), subdirs,
            chunksize=int(lendir/worker_count))

def main():
    arguments = get_cmd_line()
    '''
    arguments = {'basedir': '/home/caio/Documentos/COVID-19/DockFlow_base',
                 'targetdir': '/home/caio/Documentos/COVID-19/v2013-core',
                 'software': 'vina',
                 'protocol': 'ex8',
                 'processors': os.cpu_count(),
                 'padding': 2.0,
                 'additional': None}
    '''
    directory_processor(arguments['basedir'],
            arguments['targetdir'], arguments['software'],
            arguments['protocol'], arguments['processors'],
            arguments['padding'], arguments['additional'])

if __name__=='__main__': main()
