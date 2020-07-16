#!/bin/bash

BASEDIR="/home/caio/Documentos/COVID-19/DockFlow_base"

TARGETDIR="${BASEDIR}/pdbbind-2019"
SOFTWARE="vina"
PROTOCOL="ex8"
ADDITIONAL="-ex 8"
PROCESSORS=$(nproc)
PADDING=2

for TARGET in ${TARGETDIR}/* ; do
    TARGET=$(basename "$TARGET")
    echo "./DockFlow.py -p ${TARGETDIR} \
        --protocol ${TARGET}_${SOFTWARE}_${PROTOCOL} \
        --software ${SOFTWARE} \
        -r ${TARGETDIR}/${TARGET}/${TARGET}_protein.pdb \
        -c ${TARGETDIR}/${TARGET}/${TARGET}_ligand.mol2 \
        $(./binding_box.py ${TARGETDIR}/${TARGET}/${TARGET}_ligand.mol2 --padding $PADDING) \
        ${ADDITIONAL}"
done > dock.xargs

cat dock.xargs | xargs -P${PROCESSORS} -I '{}' bash -c '{}' > dock.log
