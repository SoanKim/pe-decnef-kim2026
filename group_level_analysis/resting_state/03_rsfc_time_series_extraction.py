#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File name: 03_rsfc_time_series_extraction.py

# This script applies the native masks generated in the previous step, filters the BOLD signal to isolate resting-state frequencies,
# standardizes the signal, and computes the Pearson correlatios between the Midline Cingulate and the pgACC.

import os
import numpy as np
import pandas as pd
import nibabel as nib
from nilearn.maskers import NiftiMasker
from scipy.stats import pearsonr

PARTICIPANTS_DIR = "/[put dir here]/participants"
PRE_NF_DIR = "/[put dir here]/bidscoin_resting_before_NF/bidsfolder"

PE_IDS = [6, 14, 18, 24, 25, 26, 35, 38, 39, 40, 42, 43, 47, 54]
NPE_IDS = [5, 9, 15, 17, 22, 27, 28, 29, 41, 46, 48, 50, 51, 53]
ALL_SUBJECTS = PE_IDS + NPE_IDS

TR = 1.1  # Our multi-echo setup  
LOW_PASS = 0.1   # Keep slow resting-state frequencies
HIGH_PASS = 0.01 # Remove ultra-slow drift

output_csv = os.path.join(PARTICIPANTS_DIR, "Resting_State_Connectivity", "Pre_NF_Connectivity_Results.csv")
os.makedirs(os.path.dirname(output_csv), exist_ok=True)

def extract_time_series():
    print("--- Starting Native Time-Series Extraction ---")
    
    results = []

    for subject_id in ALL_SUBJECTS:
        subj_str = f"subject-{subject_id}"
        print(f"\nProcessing {subj_str}...")
        
        func_file = os.path.join(PRE_NF_DIR, subj_str, "func/desc-denoised_bold.nii.gz")
        rs_align_dir = os.path.join(PARTICIPANTS_DIR, subj_str, "resting_state_alignment")
        cing_mask = os.path.join(rs_align_dir, "Cingulate_native_mask.nii.gz")
        pgacc_mask = os.path.join(rs_align_dir, "pgACC_native_mask.nii.gz")
        
        if not os.path.exists(func_file) or not os.path.exists(cing_mask) or not os.path.exists(pgacc_mask):
            print(f"  -> WARNING: Missing functional data or masks for {subj_str}. Skipping.")
            results.append({"Subject": subj_str, "Group": "Unknown", "rsFC_Correlation": "MISSING"})
            continue
            
        group_label = "PE" if subject_id in PE_IDS else "NPE"

        try:
            cing_masker = NiftiMasker(mask_img=cing_mask, target_affine=func_file, detrend=True, standardize='zscore_sample', low_pass=LOW_PASS, high_pass=HIGH_PASS, t_r=TR)
            pgacc_masker = NiftiMasker(mask_img=pgacc_mask, detrend=True, standardize='zscore_sample', 
                                       low_pass=LOW_PASS, high_pass=HIGH_PASS, t_r=TR)
            
            # fit_transform: 2D array (timepoints, voxels)
            print("  -> Extracting and filtering Midline Cingulate...")
            cing_data = cing_masker.fit_transform(func_file)
            cing_mean_ts = np.mean(cing_data, axis=1)
            
            print("  -> Extracting and filtering pgACC...")
            pgacc_data = pgacc_masker.fit_transform(func_file)
            pgacc_mean_ts = np.mean(pgacc_data, axis=1)
            
            r_value, p_value = pearsonr(cing_mean_ts, pgacc_mean_ts)
            print(f"  -> SUCCESS! rsFC Correlation (r): {r_value:.4f}")
            
            results.append({
                "Subject": subj_str,
                "Group": group_label,
                "rsFC_Correlation": r_value
            })
            
        except Exception as e:
            print(f"  -> ERROR during extraction for {subj_str}: {e}")
            results.append({"Subject": subj_str, "Group": group_label, "rsFC_Correlation": "ERROR"})

    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)
    
    print(f"\n--- ALL DONE! ---")
    print(f"Connectivity results saved to: {output_csv}")

if __name__ == "__main__":
    extract_time_series()
