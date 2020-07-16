#!/usr/bin/env python3
# coding: utf-8
# Config

import os
import pickle
import gzip

def get_indexes(mol2) :
    if os.path.isfile('ZINC.pklz') :
        pickle_in  = gzip.open("ZINC.pklz","rb")
        index_list = pickle.load(pickle_in) 
    else:
        print(f'Indexing {mol2}, please wait')
        n=0
        index_list={}
        with open(mol2,'r') as f :
            line = f.readline()
            while line:
                if line.startswith('@<TRIPOS>MOLECULE') :
                    n+=1
                    if n % 100 == 0:
                        print(n,end='\r')
                    ligand=f.readline().split()[0]
                    index_list[ligand]=f.tell()
                line = f.readline()
        pickle_out = gzip.open("ZINC.pklz","wb")
        pickle.dump(index_list, pickle_out)
        pickle_out.close()
    return index_list

def seek_to_write_mol2_from_index(mol2, ligand, index_position) :
    molecule=[]
    molecule.append(f'''@<TRIPOS>MOLECULE
{ligand}''')
    with open(mol2,'r') as f :
        f.seek(index_position)
        line = f.readline()
        while line :
            if line.startswith('@<TRIPOS>MOLECULE') :
                break
            molecule.append(line)
            line=f.readline()
    return molecule

def read_to_find_mol2(mol2, ligand) :
    molecule=[]
    molecule.append(f'''@<TRIPOS>MOLECULE
{ligand}''')
    with open(mol2,'r') as f :
        line=f.readline()
        while not line.startswith(ligand):
            line=f.readline()
        line=f.readline()
        while line :
            if line.startswith('@<TRIPOS>MOLECULE') :
                break
            molecule.append(line)
            line=f.readline()
    return molecule
    
def main():
    # Done indexing
    import time
    ligand = 'ZINC000224862372'
    mol2 = 'test.mol2'
    t0 = time.time()
    index_list = get_indexes(mol2)
    t1 = time.time()-t0
    print('Done indexing')
    t2 = time.time()
    molecule = seek_to_write_mol2_from_index(mol2, ligand, index_list[ligand])
    t2 = time.time()-t2
    # print(molecule)
    t3 = time.time()
    molecule = read_to_find_mol2(mol2, ligand)
    t3 = time.time()-t3
    t0 = t1+t2+t3
    # print(molecule)
    print(f'\nIndexing: {t1}s\nSeek: {t2}s\nRead: {t3}s\nTotal: {t0}s')

if __name__=='__main__': main()
