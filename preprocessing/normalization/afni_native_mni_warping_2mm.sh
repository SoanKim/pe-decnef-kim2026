#!/bin/bash
# FILENAME: afni_native_mni_warping_2mm.sh
# It takes searchlight results from their native acquisition resolution (3 mm) and resamples them into the standard MNI152 resolution (2 mm)..
# This is the finalized AFNI-native pipeline demonstrating the shift from FSL to 3dWarp and align_epi_anat.py

subjects=( 5 6 9 14 15 17 18 22 24 25 26 27 28 29 35 38 39 40 41 42 43 46 47 48 50 51 53 54 )

# Template path
TEMPLATE_PATH="/opt/afni/linux_openmp_64/MNI152_2009_template.nii.gz"

# The filename of the 3mm native searchlight result
SEARCHLIGHT_NAME="searchlight_result.nii" 

module load afni/latest
export OMP_NUM_THREADS=4

echo "======================================================================"
echo "STARTING MASTER PIPELINE (Deoblique -> Align -> Warp -> 2mm Output)"
echo "Target Searchlight File: $SEARCHLIGHT_NAME"
echo "Logs will be saved to: processing_log.txt in each subject folder."
echo "======================================================================"

for id in "${subjects[@]}"; do
    subj="subject-${id}"
    base_dir="/[put base_dir here]/${subj}"
    work_dir="${base_dir}/decoding_dice2decnef"
    
    log_file="${base_dir}/processing_log.txt"

    {
        echo "------------------------------------------------"
        echo "PROCESSING: ${subj}"
        echo "Time started: $(date)"
        echo "------------------------------------------------"

        raw_brain="${base_dir}/decoder_construction/data/${subj}/raw/T1/output_brain.nii"
        if [ ! -f "$raw_brain" ]; then raw_brain="${raw_brain}.gz"; fi
        
        sbref_file="${base_dir}/sbref.nii"
        
        deob_file="${base_dir}/output_brain_DEOB.nii"
        searchlight_input="${work_dir}/${SEARCHLIGHT_NAME}"
        searchlight_output="${work_dir}/${SEARCHLIGHT_NAME%.*}_MNI_2mm.nii"

        mkdir -p "$work_dir"
        cd "$base_dir" || exit

        # --- STEP 1: DEOBLIQUE T1 ---
        if [ ! -f "$deob_file" ]; then
            echo "  -> Step 1: Creating Deobliqued T1..."
            if [ -f "$raw_brain" ]; then
                 3dWarp -deoblique -prefix "$deob_file" "$raw_brain" -overwrite
            else
                 echo "     ERROR: Raw T1 ($raw_brain) not found. Skipping subject."
                 continue
            fi
        else
            echo "  -> Step 1: Deobliqued T1 exists. Proceeding."
        fi

        # --- STEP 2: UNIFIZE EPI ---
        echo "  -> Step 2: Unifizing EPI..."
        3dLocalUnifize -input "$sbref_file" \
                       -prefix "${work_dir}/epi_base_vol0_LU.nii" \
                       -overwrite

        # --- STEP 3: ALIGN T1 to EPI ---
        echo "  -> Step 3: Aligning (lpc+ZZ)..."
        align_epi_anat.py -anat "$deob_file" \
            -epi "${work_dir}/epi_base_vol0_LU.nii" \
            -epi_base 0 -epi_strip 3dAutomask -cost lpc+ZZ \
            -volreg off -tshift off -suffix _al -overwrite

        # --- STEP 4: CALCULATE WARP TO MNI ---
        echo "  -> Step 4: Calculating Auto-Warp (approx 10-15 mins)..."
        auto_warp.py -base "${TEMPLATE_PATH}" \
                     -input "$deob_file" \
                     -skull_strip_input no \
                     -overwrite

        # --- STEP 5: APPLY WARP TO SEARCHLIGHT ---
        echo "  -> Step 5: Warping Searchlight Data to MNI (2mm)..."
        
        if [ -f "awpy/anat.un.aff.qw_WARP.nii" ] && [ -f "$searchlight_input" ]; then
            
            # Using specific formatting to avoid trailing space errors
            3dNwarpApply -nwarp "awpy/anat.un.aff.qw_WARP.nii awpy/anat.un.aff.Xat.1D" \
                -source "$searchlight_input" \
                -master "${TEMPLATE_PATH}" \
                -dxyz 2.0 2.0 2.0 \
                -prefix "$searchlight_output" \
                -overwrite
                
            echo "     SUCCESS: Created $searchlight_output"
        else
            echo "     WARNING: Could not warp searchlight."
            if [ ! -f "$searchlight_input" ]; then echo "     - Missing Input: $searchlight_input"; fi
            if [ ! -f "awpy/anat.un.aff.qw_WARP.nii" ]; then echo "     - Missing Warp: awpy/anat.un.aff.qw_WARP.nii"; fi
        fi

        # --- QC STEP ---
        echo "  -> Step QC: Creating MNI EPI for visual check..."
        3dNwarpApply -nwarp "awpy/anat.un.aff.qw_WARP.nii awpy/anat.un.aff.Xat.1D" \
                -source "${work_dir}/epi_base_vol0_LU.nii" \
                -master "${TEMPLATE_PATH}" \
                -dxyz 2.0 2.0 2.0 \
                -prefix "${work_dir}/epi_base_vol0_LU_mni.nii" \
                -overwrite

        echo "Subject Complete at: $(date)"
        
    } 2>&1 | tee "$log_file" 

done

echo "======================================================================"
echo "PIPELINE COMPLETE."
echo "======================================================================"
