def get_indexes(arguments) :
    '''
    Generate/read an gziped pickle file containing the "byte" index 
    for each molecule in a .mol2 file for fast future access.
    '''
    import os
    import pickle
    import gzip

    index_file=os.path.join(arguments['project'],'DockFlow',arguments['protocol'],'.ligands')

    if os.path.isfile(index_file) :
        print(f'Reading index file: {index_file}' )
        pickle_in  = gzip.open(index_file,"rb")
        index_list = pickle.load(pickle_in) 
  
    else:
        print(f'Generating index file: {index_file}. Please wait')
        index_list={}
        with open(arguments['compounds'],'r') as f :
            while True:
                line = f.readline()
                if not line : break
                if line.startswith('@<TRIPOS>MOLECULE') :
                    ligand=f.readline().split()[0]
                    index_list[ligand]=f.tell()

        print(f'Writting index file: {index_file} ' )
        pickle_out = gzip.open(index_file,"wb")
        pickle.dump(index_list, pickle_out,protocol=-1)
        pickle_out.close()

    return index_list



def seek_mol2(mol2,ligand,index_position,nligands) :
    '''
    Seek the BIG.mol2 file to the byte indicated by "index_position".
    Then return as many molecules as indicated by "nligands"
    '''
    n=1
    molecule=[]
    molecule.append(f'''@<TRIPOS>MOLECULE
{ligand}
''')
    with open(mol2,'r') as f :
        f.seek(index_position)        
        while n <= nligands :
            line=f.readline()
            if line.startswith('@<TRIPOS>MOLECULE') :
                n+=1 
            if not line : 
                break
            molecule.append(line)
    return molecule[:-1]



def write_mol2(molecule,filename) :
    '''
    Write a molecule to an certain filename.
    '''
    with open(filename,'w') as f :
        for line in molecule :
            f.write(line)





def get_docked_list(arguments,ligand_list) :
    import shutil
    import os
    import pickle
    import gzip

    # Set checkpoint file
    index_file=os.path.join(arguments['project'],'DockFlow',arguments['protocol'],'.docked')      

    # If checkpoint file doesn't exist, docking list is empty.
    if os.path.isfile(index_file) :
        print(f'Reading index file: {index_file}' )
        pickle_in  = gzip.open(index_file,"rb")
        docked_list = pickle.load(pickle_in)    
    else :
        docked_list=[] 

# Compare ligand list with current docked list.
    dock_list  = list(set(ligand_list) - set(docked_list) ) 

# Update docked list.
    if arguments['software'] in ['vina','qvina','smina'] :
        ligand_name='out.pdbqt'

        for ligand in dock_list :
            filename=os.path.join(arguments['project'],
                                  'DockFlow',
                                  arguments['protocol'],
                                  ligand,
                                  ligand_name)

            if os.path.isfile( filename ) :
                docked_list.append(ligand)

    else :
        
        for ligand in dock_list :

            path=os.path.join(arguments['project'],
                            'DockFlow',
                            arguments['protocol'],
                            ligand,
                            'dock')

            if os.path.isdir(path) :
                if os.path.isfile( os.path.join(path,'bestranking.csv') ):
                    if os.stat( os.path.join(path,'bestranking.csv')).st_size == 0 :
                        shutil.rmtree(path)
                    else:
                        docked_list.append(ligand)
                else :
                    shutil.rmtree(path)

# Write an updated index file for docked compounds.
    print(f'Writting index file: {index_file} ' )
    pickle_out = gzip.open(index_file,"wb")
    pickle.dump(docked_list, pickle_out,protocol=-1)
    pickle_out.close()

# Now, after update, update list of compounds to dock.
    dock_list  = list(set(ligand_list) - set(docked_list) ) 

    return dock_list # List of compounds to dock