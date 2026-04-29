#!/usr/bin/env python
# -*- coding: utf-8 -*-

# File name: 01_rsfc_alignment_bridge.py

# Participants rarely have their heads in the same position across multiple scanning days. 
# It extracts the first frame of the raw resting-state scan and calculates a specific alignment matrix using align_epi_anat.py to link the native resting-state space to the anatomical T1 space. 
# It also includes the crucial -epi2anat, -giant_move, and lpc+ZZ parameters needed to salvage difficult alignments.


import os

PARTICIPANTS_DIR = "/[put dir here]/participants"
PRE_NF_DIR = "/[put dir here]/bidscoin_resting_before_NF/bidsfolder"

PE_IDS = [6, 14, 18, 24, 25, 26, 35, 38, 39, 40, 42, 43, 47, 54]
NPE_IDS = [5, 9, 15, 17, 22, 27, 28, 29, 41, 46, 48, 50, 51, 53]
ALL_SUBJECTS = PE_IDS + NPE_IDS

def calculate_rs_alignment(subject_id):
    subj_str = f"subject-{subject_id}"
    print(f"\n--- Calculating RS Bridge Matrix for {subj_str} (Skipping SkullStrip) ---")
    
    native_raw = os.path.join(PRE_NF_DIR, subj_str, "func/desc-denoised_bold.nii.gz")
    
    if subject_id == 29: # rescued participant (refer to my rescue scripts)
        anat_file = os.path.join(PARTICIPANTS_DIR, subj_str, "awpy_FINAL_FIX/anat.un.nii")
    else:
        anat_file = os.path.join(PARTICIPANTS_DIR, subj_str, "awpy/anat.un.nii")
        
    if not os.path.exists(anat_file):
        anat_file += ".gz"
        
    if not os.path.exists(native_raw) or not os.path.exists(anat_file):
        print(f"Warning: Missing data for {subj_str}.")
        return

    rs_align_dir = os.path.join(PARTICIPANTS_DIR, subj_str, "resting_state_alignment")
    os.makedirs(rs_align_dir, exist_ok=True)
    
    rs_base = os.path.join(rs_align_dir, "rs_base.nii.gz")
    if not os.path.exists(rs_base):
        os.system(f"3dTcat -prefix {rs_base} \"{native_raw}[0]\" -overwrite")

    cmd = (
        f"align_epi_anat.py "
        f"-anat {anat_file} "
        f"-epi {rs_base} "
        f"-epi_base 0 "
        f"-epi2anat "
        f"-giant_move "
        f"-anat_has_skull no "
        f"-epi_strip None "
        f"-volreg off "
        f"-tshift off "
        f"-overwrite"
    )
    
    old_wd = os.getcwd()
    os.chdir(rs_align_dir)
    os.system(cmd)
    os.chdir(old_wd)
    
    matrix_path = os.path.join(rs_align_dir, "rs_base_al_mat.aff12.1D")
    if os.path.exists(matrix_path):
        print(f"SUCCESS: Bridge matrix created at {matrix_path}")
    else:
        print(f"FAILED: Alignment failed for {subj_str}.")

if __name__ == "__main__":
    for subj in ALL_SUBJECTS:
        calculate_rs_alignment(subj)
