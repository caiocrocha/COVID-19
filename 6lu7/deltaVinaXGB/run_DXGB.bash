#!/bin/bash

echo "python ~/Downloads/deltaVinaXGB/DXGB/run_DXGB.py --runfeatures --datadir /home/caio/Documentos/COVID-19/6lu7/deltaVinaXGB/ligand_A_All --pdbid crystal_redock_e8_er3_1 --average
python ~/Downloads/deltaVinaXGB/DXGB/run_DXGB.py --runfeatures --datadir /home/caio/Documentos/COVID-19/6lu7/deltaVinaXGB/ligand_A_All --pdbid crystal_redock_e24_er3_1 --average
python ~/Downloads/deltaVinaXGB/DXGB/run_DXGB.py --runfeatures --datadir /home/caio/Documentos/COVID-19/6lu7/deltaVinaXGB/ligand_A_All --pdbid crystal_redock_e32_er3_1 --average
python ~/Downloads/deltaVinaXGB/DXGB/run_DXGB.py --runfeatures --datadir /home/caio/Documentos/COVID-19/6lu7/deltaVinaXGB/ligand_B_All --pdbid crystal_redock_e8_er3_1 --average
python ~/Downloads/deltaVinaXGB/DXGB/run_DXGB.py --runfeatures --datadir /home/caio/Documentos/COVID-19/6lu7/deltaVinaXGB/ligand_B_All --pdbid crystal_redock_e24_er3_1 --average
python ~/Downloads/deltaVinaXGB/DXGB/run_DXGB.py --runfeatures --datadir /home/caio/Documentos/COVID-19/6lu7/deltaVinaXGB/ligand_B_All --pdbid crystal_redock_e32_er3_1 --average
python ~/Downloads/deltaVinaXGB/DXGB/run_DXGB.py --runfeatures --datadir /home/caio/Documentos/COVID-19/6lu7/deltaVinaXGB/ligand_A_AllIntoOne --pdbid 6lu7 --average
python ~/Downloads/deltaVinaXGB/DXGB/run_DXGB.py --runfeatures --datadir /home/caio/Documentos/COVID-19/6lu7/deltaVinaXGB/ligand_B_AllIntoOne --pdbid 6lu7 --average" > run_DXGB.xargs

cat run_DXGB.xargs | xargs -P12 -I '{}' bash -c '{}' > run_DXGB.log
