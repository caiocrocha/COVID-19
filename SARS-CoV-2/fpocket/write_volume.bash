PROTEIN=$(awk '/Pocket 10 /{for (i=1; i<=7; i++) {getline}{print $3}}' 6lu7_protein_out/6lu7_protein_info.txt)
PROTEIN_LIG=$(awk '/Pocket 3 /{for (i=1; i<=7; i++) {getline}{print $3}}' 6lu7_fitted_out/6lu7_fitted_info.txt)

echo "volume.txt"
echo "VOL PROTEIN : $PROTEIN" | tee volume.txt
echo "VOL PROTEIN W/ LIGAND : $PROTEIN_LIG" | tee -a volume.txt

DELTA_VOL=$(echo "$PROTEIN-$PROTEIN_LIG" | bc)
echo "DELTA VOL : $DELTA_VOL" | tee -a volume.txt
