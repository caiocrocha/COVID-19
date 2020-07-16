# Functions -------------------------------------------------------------------
# Need to have imports here.
import os
import pickle
from progress.bar import Bar


def write_header() :

    print('''
------------------------------------------------
| ChemFlow - Computational Chemistry WorkFlows |
|                              www.chemflow.cc |
------------------------------------------------''')


def write_summary(project,
                  protocol,
                  compounds,
                  nligands,overwrite) :

    overwrite_warning=''
    if overwrite :
        overwrite_warning='(Overwrite)'

    print(f'''
# Collecting PLANTS results

 Project : {project}.chemflow
Protocol : {protocol}
 Ligands : {nligands}
''')

    print('''
Please cite us:
Diego E. B. Gomes, Cédric Bouysset, Marco Cecchini. Bioinformatics, 2020 
        ''')


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


def write_ligand_list(project,
                      protocol,
                      compounds,
                      ligand_list) :
    # Write down a picke file. It will make things faster latter.
    with open( os.path.join( project,'LigFlow','.ligands'),'wb') as f :
        pickle.dump(ligand_list,f)


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


def split_mol2(project,compounds,nosplit,nmol):
    
    out_dir = os.path.join(project,'LigFlow','originals')
      
    if os.path.isdir(out_dir) and nosplit  :
        return
    else :
        print(f"splitting {compounds} to {out_dir}")


    if not os.path.isdir(out_dir):
            os.makedirs(out_dir,exist_ok=True)
    

    bar = Bar('LigFlow :', max=nmol)


    f = open(compounds,"r")

    line=''
    while not line.startswith("@<TRIPOS>MOLECULE") :
        line=f.readline()

    #weird encoding may result in a python stop. using os.fstat.
    while not f.tell() == os.fstat(f.fileno()).st_size:
            if line.startswith("@<TRIPOS>MOLECULE"):
                    molecule = []
                    molecule.append(line)
                    line = f.readline()
                    line=line.split()[0]
                    molecule_id=line
                    bar.next()

            while not line.startswith("@<TRIPOS>MOLECULE"):
                    molecule.append(line)
                    line = f.readline()

                    if f.tell() == os.fstat(f.fileno()).st_size:
                            molecule.append(line)
                            break
            molecule[-1] = molecule[-1].rstrip()

            out_mol2 = os.path.join(out_dir,molecule_id) + '.mol2'

            if not os.path.isfile(out_mol2):
                    out_file = open(out_mol2,"w")

                    for x in molecule:
                            out_file.write(x)

                    out_file.write('\n')
                    out_file.close()

    f.close()
    bar.finish()

def Diff(li1, li2):
    return (list(set(li1) - set(li2)))
