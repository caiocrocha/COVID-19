if [ ! -f all_final.mol2 ] ; then
    gunzip all_final.mol2.gz
fi

DockFlow_clean.py \
--project reni \
--protocol qvina \
--receptor protein.pdb \
--ligand all_final.mol2 \
--center -7.449 -15.106 -9.893 \
qvina \
--size 18.530 18.022 13.248 

DockFlow_clean.py \
--project reni \
--protocol vina \
--receptor protein.pdb \
--ligand all_final.mol2 \
--center -7.449 -15.106 -9.893 \
vina \
--size 18.530 18.022 13.248

DockFlow_clean.py \
--project reni \
--protocol smina \
--receptor protein.pdb \
--ligand all_final.mol2 \
--center -7.449 -15.106 -9.893 \
smina \
--size 18.530 18.022 13.248

DockFlow_clean.py \
--project reni \
--protocol plants \
--receptor protein.pdb \
--ligand all_final.mol2 \
--center -7.449 -15.106 -9.893 \
plants \
--radius 11

