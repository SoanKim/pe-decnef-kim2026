#!/usr/bin/env python
# -*- coding: utf-8 -*-
# FIle name: 01b_rsfc_alignment_rescue.py
# To resolve any raw data geometric issues, 
# it applies the critical lpc+ZZ and -align_centers yes parameters 
# to save native space alignment before the start of the pipeline.


import os
import subprocess

PARTICIPANTS_DIR = "/[put_dir_here]/participants"
POST_NF_DIR = "/[put_dir_here]/bidscoin_resting_after_NF/bidsfolder"

FAILED_SUBJECTS = [22, 24, 26, 51]

def rescue_day5_alignment():
    print("--- Starting DAY 5 Alignment Rescue ---")
    
    for subject_id in FAILED_SUBJECTS:
        subj_str = f"subject-{subject_id}"
        print(f"\n[RESCUE] Processing {subj_str}...")
        
        rs_align_dir = os.path.join(PARTICIPANTS_DIR, subj_str, "day5_resting_state_alignment")
        rs_base = os.path.join(rs_align_dir, "day5_rs_base.nii.gz")
        
        anat_file = os.path.join(PARTICIPANTS_DIR, subj_str, "awpy/anat.un.nii")
        if not os.path.exists(anat_file) and os.path.exists(anat_file + ".gz"):
            anat_file += ".gz"
            
        if not os.path.exists(rs_base) or not os.path.exists(anat_file):
            print(f"  -> ERROR: Missing base files for {subj_str}. Cannot rescue.")
            continue
          
        cmd = (
            f"align_epi_anat.py "
            f"-anat {anat_file} "
            f"-epi {rs_base} "
            f"-epi_base 0 "
            f"-epi2anat "
            f"-giant_move "
            f"-align_centers yes "
            f"-cost lpc+ZZ "
            f"-anat_has_skull no "
            f"-epi_strip 3dAutomask "
            f"-volreg off "
            f"-tshift off "
            f"-overwrite"
        )
        
        old_wd = os.getcwd()
        os.chdir(rs_align_dir)
        print(f"  -> Running upgraded AFNI rescue (lpc+ZZ). This may take a few minutes...")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        os.chdir(old_wd)
        
        matrix_path = os.path.join(rs_align_dir, "day5_rs_base_al_mat.aff12.1D")
        if os.path.exists(matrix_path) and result.returncode == 0:
            print(f"  -> SUCCESS: Rescued {subj_str}!")
        else:
            print(f"  -> FAILED: Rescue did not work for {subj_str}. AFNI Error:")
            print('\n'.join(result.stderr.split('\n')[-10:]))

    print("\n--- RESCUE ATTEMPT COMPLETE ---")

if __name__ == "__main__":
    rescue_day5_alignment()
