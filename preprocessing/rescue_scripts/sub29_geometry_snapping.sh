#!/bin/bash
# FILENAME: sub29_geometry_snapping.sh
# It resolves the massive spatial origin displacement using 3dresample by forcing Subject 29's functional files to match the master file's grid and origin before applying the MNI warp.

subj="subject-29"
# INPUT: Standard skull-stripped file
raw_anat="/[put anat path here]/${subj}/raw/T1/output_brain.nii"
template="/opt/afni/linux_openmp_64/MNI152_2009_template.nii.gz"
base_dir="/[put base dir here]/participants/${subj}"
searchlight_dir="${base_dir}/decoding_dice2decnef/searchlight_hitrate"

output_warp_dir="${base_dir}/awpy_FINAL_FIX"
clean_anat="${base_dir}/anatomy/highres_clean_RPI.nii.gz"

LOG_DIR="/[log dir here]/participants/logs"
mkdir -p "$LOG_DIR"
log_file="${LOG_DIR}/${subj}_FINAL_FIXED_log.txt"

echo "========================================================"
echo "RUNNING FINAL FIX (RESAMPLE METHOD) FOR SUBJECT 29"
echo "Log saved to: $log_file"
echo "========================================================"

{
    echo "Time: $(date)"
    echo "Subject: $subj"
    echo "------------------------------------------------"

    # ======================================================
    # PART 1: PREPARE ANATOMY
    # ======================================================
    if [ ! -f "$clean_anat" ]; then
        echo "[STEP 1] Sanitizing Anatomy Header..."
        mkdir -p "${base_dir}/anatomy"
        
        if [ ! -f "$raw_anat" ]; then
            echo "[CRITICAL ERROR] Skull-stripped file not found at: $raw_anat"
            exit 1
        fi

        # Fix Tilt and Orientation
        3dWarp -deoblique -prefix temp_deoblique.nii.gz "$raw_anat"
        3dresample -orient RPI -prefix "$clean_anat" -inset temp_deoblique.nii.gz
        rm temp_deoblique.nii.gz
        echo "   [OK] Created clean anatomy."
    else
        echo "[STEP 1] Clean anatomy already exists. Skipping."
    fi

    # ======================================================
    # PART 2: CALCULATE WARP
    # ======================================================
    if [ ! -d "$output_warp_dir" ]; then
        echo "[STEP 2] Calculating Warp..."
        auto_warp.py -base "$template" \
                     -input "$clean_anat" \
                     -skull_strip_input no \
                     -output_dir "$output_warp_dir" \
                     -overwrite
    else
        echo "[STEP 2] Warp folder exists. Using existing calculation."
    fi

    if [ ! -f "${output_warp_dir}/anat.un.aff.qw_WARP.nii" ]; then
        echo "[FAIL] Warp file not found."
        exit 1
    fi

    # ======================================================
    # PART 3: MATCH GEOMETRY AND WARP
    # ======================================================
    echo "[STEP 3] Processing Functional Files..."
    cd "$searchlight_dir" || exit

    master_file="dice2decnef_searchlight_results_logistic_probs_radius_4.nii.gz"
    
    if [ ! -f "$master_file" ]; then
        echo "[CRITICAL] Main 'Total' file missing. Cannot proceed."
        exit 1
    fi
    
    # Ensure Master itself is de-oblique
    3drefit -deoblique "$master_file"

    suffixes=("" "_session-1" "_session-2" "_session-3")

    for s_id in "${suffixes[@]}"; do
        source="dice2decnef_searchlight_results_logistic_probs_radius_4${s_id}.nii.gz"
        output="dice2decnef_searchlight_results_logistic_probs_radius_4${s_id}_MNI_2mm.nii.gz"
        
        if [ -f "$source" ]; then
            echo "------------------------------------------------"
            echo "Processing: $source"
            
            warp_input="$source"
            
            # [A] SNAP GEOMETRY (The Fix)
            if [ "$source" != "$master_file" ]; then
                echo "   [SNAP] Resampling to match Master geometry..."
                # Resample: Match Master's Grid, Origin, and Orientation
                3dresample -master "$master_file" \
                           -inset "$source" \
                           -prefix temp_snapped.nii.gz \
                           -overwrite
                           
                warp_input="temp_snapped.nii.gz"
            fi
            
            # [B] APPLY WARP
            echo "   [WARP] Creating MNI file from $warp_input..."
            3dNwarpApply -prefix "$output" \
                         -nwarp "${output_warp_dir}/anat.un.aff.qw_WARP.nii ${output_warp_dir}/anat.un.aff.Xat.1D" \
                         -source "$warp_input" \
                         -master "$template" \
                         -dxyz 2.0 2.0 2.0 \
                         -overwrite
            
            if [ "$warp_input" == "temp_snapped.nii.gz" ]; then
                rm temp_snapped.nii.gz
            fi
                         
            echo "   [DONE] Success."
        fi
    done

    echo "========================================================"
    echo "FINISHED. Check alignment in FSLeyes."

} 2>&1 | tee "$log_file"
