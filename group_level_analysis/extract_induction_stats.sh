#!/bin/bash
# FILENAME: extract_induction_stats.sh
# GOAL: Extract mean induction values from the Group ROI.

module load fsl/6.0.3

PARTICIPANTS_DIR="/[put dir here]/participants"
ROI_MASK="${PARTICIPANTS_DIR}/group_stats_ROI/ROI_Mask_Top5pct.nii.gz"
OUTPUT_CSV="${PARTICIPANTS_DIR}/group_stats_ROI/FINAL_INDUCTION_RESULTS.csv"

# Complete Subject List
subjects=( 5 6 9 14 15 17 18 22 24 25 26 27 28 29 35 38 39 40 41 42 43 46 47 48 50 51 53 54 )

echo "========================================================"
echo "EXTRACTING INDUCTION VALUES"
echo "ROI Used: ROI_Mask_Top5pct.nii.gz"
echo "========================================================"

# Header for CSV
echo "Subject,Session1,Session2,Session3,Total_Induction" > "$OUTPUT_CSV"

for id in "${subjects[@]}"; do
    subj="subject-${id}"
    data_dir="${PARTICIPANTS_DIR}/${subj}/decoding_dice2decnef/MNI_induction_sessions"
    
    # Initialize variables in case files are missing
    val_s1="NaN"
    val_s2="NaN"
    val_s3="NaN"
    val_tot="NaN"

    echo "Processing $subj..."

    if [ -d "$data_dir" ]; then
        
        f1=$(find "$data_dir" -name "*session-1_MNI_2mm.nii.gz" | head -n 1)
        if [ -n "$f1" ]; then
            val_s1=$(fslmeants -i "$f1" -m "$ROI_MASK")
        fi

        f2=$(find "$data_dir" -name "*session-2_MNI_2mm.nii.gz" | head -n 1)
        if [ -n "$f2" ]; then
            val_s2=$(fslmeants -i "$f2" -m "$ROI_MASK")
        fi

        f3=$(find "$data_dir" -name "*session-3_MNI_2mm.nii.gz" | head -n 1)
        if [ -n "$f3" ]; then
            val_s3=$(fslmeants -i "$f3" -m "$ROI_MASK")
        fi

        ftot=$(find "$data_dir" -name "*radius_4_MNI_2mm.nii.gz" | head -n 1)
        if [ -n "$ftot" ]; then
            val_tot=$(fslmeants -i "$ftot" -m "$ROI_MASK")
        fi
        
    else
        echo "   [SKIP] No Induction folder found."
    fi

    echo "$subj,$val_s1,$val_s2,$val_s3,$val_tot" >> "$OUTPUT_CSV"
done

echo "========================================================"
echo "DONE."
echo "Results saved to: $OUTPUT_CSV"
echo "========================================================"
