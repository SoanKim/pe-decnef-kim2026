#!/bin/bash
# FILENAME: sub29_chain_warp_rescue.sh
# This script fixes Subject 29's misaligned Decoder Searchlight Map when moving it to MNI space.
# It runs align_epi_anat with -epi2anat to get the correct matrix direction.

module load afni/latest
module load fsl/6.0.3

SUBJ="subject-29"
BASE_DIR="[put base dir here]"
TEMPLATE="/opt/afni/linux_openmp_64/MNI152_2009_template.nii.gz"
INPUT_DIR="$(pwd)/decoder_searchlight/AUCmaps"

DECODER_MAP="${INPUT_DIR}/${SUBJ}_searchlight_AUC_LOGO_Corrected.nii.gz"
EPI_BASE="${BASE_DIR}/${SUBJ}/decoding_dice2decnef/epi_base_vol0_LU.nii"

# THE CORRECT WARP ANAT
WARP_DIR="${BASE_DIR}/${SUBJ}/awpy_FINAL_FIX"
ANAT_REF="${WARP_DIR}/anat.un.nii" 
ANAT_WARP="${WARP_DIR}/anat.un.aff.qw_WARP.nii"
ANAT_AFFINE="${WARP_DIR}/anat.un.aff.Xat.1D"

OUTPUT_FINAL="Subject_29_FINAL_RESCUE.nii.gz"

echo "========================================================"
echo "SOLVING S29: EPI -> ANAT DIRECTION"
echo "========================================================"

echo "1. Calculating alignment (EPI -> Anatomy)..."

align_epi_anat.py \
    -anat "$ANAT_REF" \
    -epi "$EPI_BASE" \
    -epi_base 0 \
    -anat_has_skull no \
    -epi_strip None \
    -giant_move \
    -epi2anat \
    -volreg off \
    -tshift off \
    -suffix _al_correct \
    -overwrite

GENERATED_MATRIX="epi_base_vol0_LU_al_correct_mat.aff12.1D"

if [ ! -f "$GENERATED_MATRIX" ]; then
    echo "ERROR: Matrix not found: $GENERATED_MATRIX"
    echo "Attempting to find any .aff12.1D file created just now..."
    GENERATED_MATRIX=$(ls *mat.aff12.1D | head -n 1)
    echo "Found: $GENERATED_MATRIX"
fi

if [ ! -f "$GENERATED_MATRIX" ]; then
    echo "FATAL: Could not locate the matrix file."
    exit 1
fi

echo "   -> Success! Using Matrix: $GENERATED_MATRIX"

# Decoder -> [Matrix] -> Anatomy -> [Affine] -> [Warp] -> MNI
echo "2. Applying Chained Warp to Decoder Map..."

3dNwarpApply \
    -prefix "$OUTPUT_FINAL" \
    -nwarp "${ANAT_WARP} ${ANAT_AFFINE} ${GENERATED_MATRIX}" \
    -source "$DECODER_MAP" \
    -master "$TEMPLATE" \
    -dxyz 2.0 2.0 2.0 \
    -overwrite \
    -quiet

rm "$GENERATED_MATRIX" 2>/dev/null
rm epi_base_vol0_LU_al_correct* 2>/dev/null

echo "========================================================"
echo "DONE. The fixed file is: $OUTPUT_FINAL"
