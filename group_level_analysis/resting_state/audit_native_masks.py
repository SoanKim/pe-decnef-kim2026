#!/usr/bin/env python
# -*- coding: utf-8 -*-

# File name: audit_native_masks.py

# This verifies the inverse warp worked correctly by counting the voxels in the native masks and generating visual overlays 
# to ensure the ROIs are correctly positioned and not "floating off target" or empty.

import os
import nibabel as nib
import numpy as np
from nilearn import plotting

PARTICIPANTS_DIR = "/[put dir here]/participants"
QC_DIR = os.path.join(PARTICIPANTS_DIR, "QC_Native_Masks")
os.makedirs(QC_DIR, exist_ok=True)

PE_IDS = [6, 14, 18, 24, 25, 26, 35, 38, 39, 40, 42, 43, 47, 54]
NPE_IDS = [5, 9, 15, 17, 22, 27, 28, 29, 41, 46, 48, 50, 51, 53]
ALL_SUBJECTS = PE_IDS + NPE_IDS

html_file = os.path.join(QC_DIR, "native_masks_report.html")

def generate_mask_qc():
    print(f"Starting automated mask QC. Outputting to: {QC_DIR}")
    
    html_content = "<html><body style='font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px;'>"
    html_content += "<h1>Native Space ROI Quality Control</h1>"

    for subject_id in ALL_SUBJECTS:
        subj_str = f"subject-{subject_id}"
        print(f"Processing {subj_str}...")
        
        rs_align_dir = os.path.join(PARTICIPANTS_DIR, subj_str, "resting_state_alignment")
        rs_master = os.path.join(rs_align_dir, "rs_base.nii.gz")
        cing_mask = os.path.join(rs_align_dir, "Cingulate_native_mask.nii.gz")
        pgacc_mask = os.path.join(rs_align_dir, "pgACC_native_mask.nii.gz")
        
        html_content += f"<h2>{subj_str}</h2>"

        if not os.path.exists(rs_master) or not os.path.exists(cing_mask) or not os.path.exists(pgacc_mask):
            print(f"  -> WARNING: Missing files for {subj_str}")
            html_content += f"<p style='color: red;'><b>MISSING FILES!</b></p><hr>"
            continue

        cing_data = nib.load(cing_mask).get_fdata()
        pgacc_data = nib.load(pgacc_mask).get_fdata()
        
        cing_voxels = np.sum(cing_data > 0)
        pgacc_voxels = np.sum(pgacc_data > 0)
        
        print(f"  -> Cingulate voxels: {cing_voxels} | pgACC voxels: {pgacc_voxels}")
        
        html_content += f"<p><b>Voxel Counts:</b> Cingulate = {cing_voxels}, pgACC = {pgacc_voxels}</p>"
        
        if cing_voxels == 0 or pgacc_voxels == 0:
            html_content += "<p style='color: red;'><b>WARNING: EMPTY MASK DETECTED!</b></p>"
            html_content += "<hr>"
            continue

        cing_img_path = os.path.join(QC_DIR, f"{subj_str}_cingulate.png")
        pgacc_img_path = os.path.join(QC_DIR, f"{subj_str}_pgACC.png")
        
        try:
            plotting.plot_roi(cing_mask, bg_img=rs_master, display_mode='ortho', 
                              title=f"{subj_str} - Cingulate", output_file=cing_img_path, 
                              draw_cross=False, cmap='autumn')
            
            plotting.plot_roi(pgacc_mask, bg_img=rs_master, display_mode='ortho', 
                              title=f"{subj_str} - pgACC", output_file=pgacc_img_path, 
                              draw_cross=False, cmap='winter')
            
            html_content += f"<h3>Midline Cingulate</h3><img src='{subj_str}_cingulate.png' style='max-width: 800px; border: 1px solid #ccc;'><br>"
            html_content += f"<h3>pgACC</h3><img src='{subj_str}_pgACC.png' style='max-width: 800px; border: 1px solid #ccc;'><br><hr>"
        except Exception as e:
            print(f"  -> ERROR plotting {subj_str}: {e}")
            html_content += f"<p style='color: red;'><b>ERROR PLOTTING IMAGES</b></p><hr>"

    html_content += "</body></html>"
    with open(html_file, "w") as f:
        f.write(html_content)
        
    print("\n--- ALL DONE! ---")

if __name__ == "__main__":
    generate_mask_qc()
