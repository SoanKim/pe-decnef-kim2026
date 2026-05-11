#!/bin/bash
# File name: sub35_dualbox_artifact_masking.sh
# It surgically remove the signal artifacts caused by the 17-degree anatomical tilt.
# Ir defines spatial boundaries, combine them using fslmaths into temp_danger_zones.nii.gz, and zero out the bright signal artifacts.

BASE_DIR="/[put base dir here]"
SUBJECT="subject-35"

INPUT_FILE="${BASE_DIR}/${SUBJECT}/decoding_dice2decnef/searchlight_hitrate/dice2decnef_searchlight_results_logistic_probs_radius_4_session-3_MNI_2mm.nii.gz"
OUTPUT_FILE="${BASE_DIR}/${SUBJECT}/decoding_dice2decnef/searchlight_hitrate/dice2decnef_searchlight_results_logistic_probs_radius_4_session-3_MNI_2mm_MASKED.nii.gz"

LOG_DIR="${BASE_DIR}/logs"
LOG_FILE="${LOG_DIR}/${SUBJECT}_masking_log.txt"
mkdir -p "$LOG_DIR"

# Box 1: RIGHT Side Artifact (The big blob)
RIGHT_MIN_X=50
RIGHT_MIN_Y=40
RIGHT_MIN_Z=50

# Box 2: LEFT Side Rim (The new artifact)
LEFT_MAX_X=40
LEFT_MIN_Z=50

THRESH=0.75

exec > >(tee -a "$LOG_FILE") 2>&1
echo "========================================"
echo "Run Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Processing $SUBJECT..."
echo "STRATEGY: Dual Box Constraint"
echo "1. Right Box: X > $RIGHT_MIN_X, Y > $RIGHT_MIN_Y, Z > $RIGHT_MIN_Z"
echo "2. Left Box:  X < $LEFT_MAX_X, Z > $LEFT_MIN_Z"

if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: Input file missing."
    exit 1
fi

TEMP_DIR=$(dirname "$INPUT_FILE")

# RIGHT Box Mask
# -roi <xmin> <xsize> <ymin> <ysize> <zmin> <zsize> ...
# -1 means "full size"
fslmaths "$INPUT_FILE" -mul 0 -add 1 \
  -roi $RIGHT_MIN_X -1 $RIGHT_MIN_Y -1 $RIGHT_MIN_Z -1 0 1 \
  "${TEMP_DIR}/temp_box_right.nii.gz"

# LEFT Box Mask
# -roi 0 <xsize> ...
# Size is LEFT_MAX_X (from 0 to 40)
fslmaths "$INPUT_FILE" -mul 0 -add 1 \
  -roi 0 $LEFT_MAX_X 0 -1 $LEFT_MIN_Z -1 0 1 \
  "${TEMP_DIR}/temp_box_left.nii.gz"

# Combine Boxes, cleaning pixels that are in Box 1 OR Box 2
fslmaths "${TEMP_DIR}/temp_box_right.nii.gz" \
  -add "${TEMP_DIR}/temp_box_left.nii.gz" \
  -bin "${TEMP_DIR}/temp_danger_zones.nii.gz"

# Identify Bright Spots
fslmaths "$INPUT_FILE" -thr $THRESH -bin "${TEMP_DIR}/temp_bright_mask.nii.gz"

# Keep bright spots ONLY if they are inside either box
fslmaths "${TEMP_DIR}/temp_bright_mask.nii.gz" \
  -mas "${TEMP_DIR}/temp_danger_zones.nii.gz" \
  "${TEMP_DIR}/temp_kill_mask.nii.gz"

# Dilate slightly to clean edges
fslmaths "${TEMP_DIR}/temp_kill_mask.nii.gz" -dilF "${TEMP_DIR}/temp_final_kill_mask.nii.gz"

# Apply the fix (Set to 0.5)
fslmaths "${TEMP_DIR}/temp_final_kill_mask.nii.gz" -binv "${TEMP_DIR}/temp_safe_mask.nii.gz"

# Zero out the artifact
fslmaths "$INPUT_FILE" -mas "${TEMP_DIR}/temp_safe_mask.nii.gz" "${TEMP_DIR}/temp_data_zeroed.nii.gz"

# Fill with 0.5
fslmaths "${TEMP_DIR}/temp_final_kill_mask.nii.gz" -mul 0.5 "${TEMP_DIR}/temp_patch.nii.gz"

# Merge
fslmaths "${TEMP_DIR}/temp_data_zeroed.nii.gz" -add "${TEMP_DIR}/temp_patch.nii.gz" "$OUTPUT_FILE"

rm "${TEMP_DIR}/temp_box_right.nii.gz" "${TEMP_DIR}/temp_box_left.nii.gz" \
   "${TEMP_DIR}/temp_danger_zones.nii.gz" "${TEMP_DIR}/temp_bright_mask.nii.gz" \
   "${TEMP_DIR}/temp_kill_mask.nii.gz" "${TEMP_DIR}/temp_final_kill_mask.nii.gz" \
   "${TEMP_DIR}/temp_safe_mask.nii.gz" "${TEMP_DIR}/temp_data_zeroed.nii.gz" \
   "${TEMP_DIR}/temp_patch.nii.gz"

echo "DONE. Artifacts in both Left and Right zones removed."
echo "Output: $OUTPUT_FILE"
echo "========================================"
