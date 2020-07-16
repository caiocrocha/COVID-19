# Using this natsorted implementation means one less package to install
# https://stackoverflow.com/questions/4836710/does-python-have-a-built-in-function-for-string-natural-sort
def natsorted(seq, key=None):
    import re
    def convert(text):
        return int(text) if text.isdigit() else text

    def alphanum(obj):
        if key is not None:
            return [convert(c) for c in re.split(r'([0-9]+)', key(obj))]
        return [convert(c) for c in re.split(r'([0-9]+)', obj)]

    return sorted(seq, key=alphanum)


def get_docked_list(project,protocol,software,ligand_list) :

    import shutil
    import os

    docked_list=[]

    if software in ['vina','qvina'] :
        ligand_name='out.pdbqt'

        for ligand in ligand_list :
            if os.path.isfile( os.path.join(project,
                                            'DockFlow',
                                            protocol,
                                            ligand,
                                            ligand_name) ) :
                docked_list.append(ligand)

    else :
        
        for ligand in ligand_list :

            path=os.path.join(project,
                              'DockFlow',
                              protocol,
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
        
    return docked_list


def get_prepared_list(project,protocol,software,ligand_list) :
    import os
    if software in ['vina','qvina'] :
        ligand_name='ligand.pdbqt'
    else :
        ligand_name='ligand.mol2'
	
    prepared_list=[]
    for ligand in ligand_list :
        if os.path.isfile( os.path.join(project,'DockFlow',protocol,ligand,ligand_name) ) :
            prepared_list.append(ligand)
            
    return prepared_list




def get_ligand_list(project,protocol,compounds) :

    ligand_list=[]

    if compounds :
        ligand_list=get_ligand_list_from_mol2(compounds)
    
    else :
        ligand_list=get_ligand_list_from_project(project,
                                                 protocol, 
                                                 compounds, 
                                                 ligand_list)
    
    return ligand_list

def get_ligand_list_from_mol2(compounds):
    '''
    Reads the compounds .mol2 file.
    '''
    ligand_list=[]
    # Get number of molecules to process.                    
    with open(compounds, 'r') as f:
        for line in f:
            if 'MOLECULE' in line:
                ligand_list.append(f.readline().split()[0])

    return ligand_list


def get_ligand_list_from_project(project,
                                 protocol,
                                 compounds,
                                 ligand_list):
    import os
    import pickle

    try : 
        if os.path.isfile(project+'/LigFlow/.ligands') :
            with open(project+'/LigFlow/.ligands','rb') as f :
                ligand_list=pickle.load(f)
        
        else :
            for ligand in next(os.walk(project+'/LigFlow/originals/'))[2] :
                ligand_list.append(ligand.split('.')[0])
        
            with open(project+'/LigFlow/.ligands','wb') as f :
                pickle.dump(ligand_list,f)
    
    except Exception as e:
        print(e.message)
        print('[Error] Could not get ligand list')
        quit()

    return ligand_list


def write_ligand_list(project,
                      protocol,
                      compounds,
                      ligand_list) :
    import os
    import pickle
    
    # Write down a picke file. It will make things faster latter.
    with open( os.path.join( project,'LigFlow','.ligands'),'wb') as f :
        pickle.dump(ligand_list,f)

