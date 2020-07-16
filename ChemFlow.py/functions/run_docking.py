def run_dockflow(arguments,index_list,dock_list) :
    import os
    from functools import partial
    from multiprocessing import Pool
    from tqdm import tqdm
    import itertools

    path=os.path.join(arguments['project'],'DockFlow',arguments['protocol'])    

    length = len(dock_list) #arguments['ndock']
    
    workers = min(os.cpu_count(), length)
    
    with Pool(workers) as pool:
        tuple(tqdm(pool.imap(partial(run_docking, 
                                     path=path,
                                     mol2=arguments['compounds'],
                                     software=arguments['software'],
                                     index_list=index_list), dock_list), total=length, unit='compounds'))

    return 

def run_docking(ligand,mol2,software,index_list,path) :
    import subprocess
    import os
    from functions.mol2_index import seek_mol2,write_mol2

    MGLTOOLS_BIN  = os.getenv('CONDA_PREFIX')+'/bin/'
    SPORES_EXEC   = os.getenv('SPORES_EXEC')
    VINA_EXEC     = os.getenv('VINA_EXEC')
    QVINA_EXEC    = os.getenv('QVINA_EXEC')
    SMINA_EXEC    = os.getenv('SMINA_EXEC')
    PLANTS_EXEC   = os.getenv('PLANTS_EXEC')

    out_dir = os.path.join(path,ligand)

    if not os.path.isdir(out_dir) :
        os.makedirs(out_dir)

    # Seek from FULL mol2 file
    molecule = seek_mol2(mol2,ligand,index_list[ligand],1)

    file_in   = f'/dev/shm/{ligand}_tmp.mol2'
    file_log  = f'/dev/shm/{ligand}.log'

    # Prepare ligand can't work with files not in current dir.
    # We're using symbolic links to /dev/shm to speed up !
    file_link = f'{ligand}_tmp.mol2'
    if not os.path.exists(file_link) :
        os.symlink(file_in, file_link)

    write_mol2(molecule,file_in)

# Prepare ligand for docking
#--------------------------------------------------------------------
    if software in ['vina','qvina','smina'] :
        file_out=f'/dev/shm/{ligand}.pdbqt'
        cmd=['python2',os.path.join(MGLTOOLS_BIN,'prepare_ligand4.py'),'-l',file_link,'-o',file_out]
    
    if software in ['plants'] :
        file_out=f'/dev/shm/{ligand}.mol2'
        cmd=[SPORES_EXEC,'--mode','complete',file_link,file_out]

    with open(file_log, "w") as file:
        try : 
            subprocess.run(cmd, stdout=file,stderr=subprocess.STDOUT)
        except :
            pass
            #print(f'''Prepare ligand failed, check log at {file_log}''')

# Cleanup prepare's temporary files
#--------------------------------------------------------------------
    if os.path.exists(file_link) :
        os.unlink(file_link)

    if os.path.exists(file_in) :
        os.remove(file_in)

    if software in ['plants'] :
        if os.path.exists(f'{ligand}_bad.mol2') :
            os.remove(f'{ligand}_bad.mol2')

    # Run docking
    if software in ['vina','qvina','smina'] :
        file_link=os.path.join(out_dir,'ligand.pdbqt')
        if not os.path.exists(file_link) :
            os.symlink(file_out, file_link)

        file_out=f'{out_dir}/out.pdbqt'
        
        if software == 'qvina' :
            VINA_EXEC=QVINA_EXEC
        if software == 'smina' :
            VINA_EXEC=SMINA_EXEC
        
        cmd=[VINA_EXEC,'--config','../config.in']

    if software in ['plants'] :
        file_in=file_out
        file_link=os.path.join(out_dir,'ligand.mol2')
        if not os.path.exists(file_link) :
            os.symlink(file_in, file_link)
        cmd=[PLANTS_EXEC,'--mode','screen','../config.in']

    with open(file_log, "w") as file:
        try : 
            subprocess.run(cmd,cwd=out_dir,stdout=file,stderr=subprocess.DEVNULL)
        except :
            #print(f'''Docking ligand failed, check log at {file_log}''')
            pass
    

# Cleanup docking's temporary files
#--------------------------------------------------------------------
    if os.path.exists(file_in):
        os.remove(file_in)

    if os.path.exists(file_link) :
        os.unlink(file_link)

    if software in ['plants'] :
        if os.path.exists(f'{ligand}_bad.mol2') :
            os.remove(f'{ligand}_bad.mol2')


    # Post-process for energies


