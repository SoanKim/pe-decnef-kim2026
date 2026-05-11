#!/usr/bin/env python
# -*- coding: utf-8 -*-

# File name: audit_rsfc_alignment.py
# Generates visual HTML reports using @snapshot_volreg to verify the alignment between the resting-state EPI and the anatomy.

import os
import subprocess

PARTICIPANTS_DIR = "/[put dir here]/participants"
PE_IDS = [6, 14, 18, 24, 25, 26, 35, 38, 39, 40, 42, 43, 47, 54]
NPE_IDS = [5, 9, 15, 17, 22, 27, 28, 29, 41, 46, 48, 50, 51, 53]
ALL_SUBJECTS = PE_IDS + NPE_IDS

QC_DIR = os.path.join(PARTICIPANTS_DIR, "QC_alignment_reports")
os.makedirs(QC_DIR, exist_ok=True)

html_file = os.path.join(QC_DIR, "alignment_report.html")

def generate_qc_report():
    print(f"Starting QC generation. Images will be saved to: {QC_DIR}")
    
    html_content = "<html><body style='font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px;'>"
    html_content += "<h1>Resting State to Anatomy Alignment QC Report</h1>"

    for subject_id in ALL_SUBJECTS:
        subj_str = f"subject-{subject_id}"
        print(f"\nProcessing {subj_str}...")
        
        if subject_id == 29:
            anat_file = os.path.join(PARTICIPANTS_DIR, subj_str, "awpy_FINAL_FIX/anat.un.nii")
        else:
            anat_file = os.path.join(PARTICIPANTS_DIR, subj_str, "awpy/anat.un.nii")
            
        if not os.path.exists(anat_file) and os.path.exists(anat_file + ".gz"):
            anat_file += ".gz"

        rs_align_dir = os.path.join(PARTICIPANTS_DIR, subj_str, "resting_state_alignment")

        aligned_epi = os.path.join(rs_align_dir, "rs_base_al+orig.HEAD")
        if not os.path.exists(aligned_epi):
            aligned_epi = os.path.join(rs_align_dir, "rs_base_al.nii.gz")
            
        out_jpeg = os.path.join(QC_DIR, f"{subj_str}_qc.jpg")

        if os.path.exists(anat_file) and os.path.exists(aligned_epi):
            cmd = f"@snapshot_volreg {anat_file} {aligned_epi} {out_jpeg}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  -> Generated JPEG for {subj_str}")
                html_content += f"<h2>{subj_str}</h2>"
                html_content += f"<img src='{subj_str}_qc.jpg' style='max-width: 800px; border: 1px solid #ccc;'><br><hr>"
            else:
                print(f"  -> AFNI Error for {subj_str}:\n{result.stderr}")
                html_content += f"<h2 style='color: red;'>{subj_str} - SNAPSHOT FAILED</h2><hr>"
        else:
            print(f"  -> Missing files for {subj_str}. Cannot generate QC.")
            html_content += f"<h2 style='color: orange;'>{subj_str} - MISSING DATA</h2><hr>"

    html_content += "</body></html>"
    with open(html_file, "w") as f:
        f.write(html_content)
        
    print(f"\n--- DONE! ---")

if __name__ == "__main__":
    generate_qc_report()
