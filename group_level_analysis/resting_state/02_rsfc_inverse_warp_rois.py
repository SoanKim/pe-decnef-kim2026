#!/usr/bin/env python
# -*- coding: utf-8 -*-

# File name: 02_rsfc_inverse_warp_rois.py
# Rather than pushing resting-state data into MNI space (which can distort the signal), 
# this script pulls the MNI ROIs (Cingulate and pgACC) down into the participant's native space. 

import os
import subprocess

PARTICIPANTS_DIR = "/[put dir here]/participants"

ROI_DIR = "/[put dir here]/ROIs"
MNI_ROIS = {
    "Cingulate": os.path.join(ROI_DIR, "midline_cingulate_MNI.nii.gz"),
    "pgACC": os.path.join(ROI_DIR, "pgACC_MNI.nii.gz")
}

PE_IDS = [6, 14, 18, 24, 25, 26, 35, 38, 39, 40, 42, 43, 47, 54]
NPE_IDS = [5, 9, 15, 17, 22, 27, 28, 29, 41, 46, 48, 50, 51, 53]
ALL_SUBJECTS = PE_IDS + NPE_IDS

def run_inverse_warp():
    print("--- Starting Native Space ROI Inverse Warping ---")
    
    for subject_id in ALL_SUBJECTS:
        subj_str = f"subject-{subject_id}"
        print(f"\nProcessing {subj_str}...")
        
        rs_align_dir = os.path.join(PARTICIPANTS_DIR, subj_str, "resting_state_alignment")
        rs_master = os.path.join(rs_align_dir, "rs_base.nii.gz") # The deobliqued native grid
        rs_bridge_matrix = os.path.join(rs_align_dir, "rs_base_al_mat.aff12.1D")
        
        # Handle S29 Giant Move vs Standard Awpy
        if subject_id == 29:
            awpy_dir = os.path.join(PARTICIPANTS_DIR, subj_str, "awpy_FINAL_FIX")
        else:
            awpy_dir = os.path.join(PARTICIPANTS_DIR, subj_str, "awpy")
            
        # The Anatomy-to-MNI affine and non-linear inverse warp files
        anat_affine = os.path.join(awpy_dir, "anat.un.aff.Xat.1D")
        mni_inv_warp = os.path.join(awpy_dir, "anat.un.aff.qw_WARPINV.nii")
        
        if not os.path.exists(mni_inv_warp) and os.path.exists(mni_inv_warp + ".gz"):
            mni_inv_warp += ".gz"

        missing_files = []
        for f in [rs_master, rs_bridge_matrix, anat_affine, mni_inv_warp]:
            if not os.path.exists(f):
                missing_files.append(f)
                
        if missing_files:
            print(f"  -> WARNING: Missing required matrices for {subj_str}. Skipping.")
            for mf in missing_files:
                print(f"     Missing: {mf}")
            continue

        for roi_name, mni_path in MNI_ROIS.items():
            out_mask = os.path.join(rs_align_dir, f"{roi_name}_native_mask.nii.gz")
            
            if not os.path.exists(mni_path):
                print(f"  -> ERROR: MNI ROI file not found: {mni_path}")
                continue
                
            if os.path.exists(out_mask):
                print(f"  -> {roi_name} native mask already exists. Skipping.")
                continue

            # MNI non-linear inverse warp (MNI -> Anat)
            # INV(Anat Affine) (Anat -> Anat unaligned)
            # INV(Bridge Matrix) (Anat -> Native RS)
            cmd = (
                f"3dNwarpApply "
                f"-prefix {out_mask} "
                f"-nwarp 'INV({rs_bridge_matrix}) INV({anat_affine}) {mni_inv_warp}' "
                f"-source {mni_path} "
                f"-master {rs_master} "
                f"-interp NN " # Nearest Neighbor: binary mask
                f"-overwrite"
            )
            
            print(f"  -> Warping {roi_name} to native space...")
            subprocess.run(cmd, shell=True, capture_output=True)
            
            if os.path.exists(out_mask):
                print(f"     SUCCESS: Saved to {out_mask}")
            else:
                print(f"     FAILED to generate {roi_name} mask.")

    print("\n--- ALL DONE! Inverse warping complete. ---")

if __name__ == "__main__":
    run_inverse_warp()
