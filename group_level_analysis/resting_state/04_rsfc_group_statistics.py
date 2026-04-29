#!/usr/bin/env python
# -*- coding: utf-8 -*-

# File name: 04_rsfc_group_statistics.py
# This script takes the individual participant delta maps (the change in connectivity pre- vs. post-training) and runs a second-level GLM comparing the PE and NPE groups. 
# It also handles spatial smoothing necessary for aligning network boundaries and generates the final statistical Z-maps thresholded at Z > 2.3.

import os
import glob
import pandas as pd
import nibabel as nib
from nilearn.glm.second_level import SecondLevelModel
from nilearn import plotting

PARTICIPANTS_DIR = "/[put dir here]/participants"
RSFC_DIR = os.path.join(PARTICIPANTS_DIR, "Resting_State_Connectivity")

WB_DIR = os.path.join(RSFC_DIR, "Whole_Brain_MNI_Maps") 
if not os.path.exists(WB_DIR):
    WB_DIR = os.path.join(RSFC_DIR, "Whole_Brain_Maps")

STATS_DIR = os.path.join(RSFC_DIR, "Whole_Brain_Statistics")
os.makedirs(STATS_DIR, exist_ok=True)

PE_IDS = [6, 14, 18, 24, 25, 26, 35, 38, 39, 40, 42, 43, 47, 54]
NPE_IDS = [5, 9, 15, 17, 22, 27, 28, 29, 41, 46, 48, 50, 51, 53]

def run_group_statistics():
    print("--- Starting Whole-Brain Group Analysis (PE vs. NPE) ---")
    
    delta_maps = []
    conditions = []
    subject_labels = []

    for subject_id in PE_IDS + NPE_IDS:
        subj_str = f"subject-{subject_id}"
        
        search_pattern = os.path.join(WB_DIR, subj_str, f"{subj_str}_Delta_Cingulate_MNI_*.nii.gz")
        found_files = glob.glob(search_pattern)
        
        if found_files:
            delta_maps.append(found_files[0])
            subject_labels.append(subj_str)
            conditions.append('PE' if subject_id in PE_IDS else 'NPE')
        else:
            print(f"  -> ERROR: Missing Delta Map for {subj_str}")

    if len(delta_maps) < 28:
        print(f"\nWARNING: Only found {len(delta_maps)} out of 28 maps. Check errors above.")
        return

    print("\n-> Building Design Matrix...")
    design_matrix = pd.DataFrame({'PE': [1 if c == 'PE' else 0 for c in conditions],
                                  'NPE': [1 if c == 'NPE' else 0 for c in conditions]}, 
                                 index=subject_labels)
    design_matrix.to_csv(os.path.join(STATS_DIR, "design_matrix.csv"))

    print("-> Fitting Second-Level GLM with 6mm smoothing...")
    # Smoothing: Align overlapping network boundaries between subjects
    second_level_model = SecondLevelModel(smoothing_fwhm=6.0)
    second_level_model = second_level_model.fit(delta_maps, design_matrix=design_matrix)

    print("-> Computing Contrast: PE > NPE...")
    z_map_pe_gt_npe = second_level_model.compute_contrast('PE - NPE', output_type='z_score')
    nib.save(z_map_pe_gt_npe, os.path.join(STATS_DIR, "Contrast_PE_greater_than_NPE_Zmap.nii.gz"))

    print("-> Computing Contrast: NPE > PE...")
    z_map_npe_gt_pe = second_level_model.compute_contrast('NPE - PE', output_type='z_score')
    nib.save(z_map_npe_gt_pe, os.path.join(STATS_DIR, "Contrast_NPE_greater_than_PE_Zmap.nii.gz"))

    print("\n-> Generating Statistical Plots...")
    
    plot_pe = os.path.join(STATS_DIR, "Plot_PE_greater_than_NPE.png")
    plotting.plot_stat_map(z_map_pe_gt_npe, threshold=2.3, display_mode='z', 
                           cut_coords=[-10, 0, 10, 20, 30, 40],
                           title="PE > NPE (\u0394 rsFC, uncorrected Z > 2.3)",
                           output_file=plot_pe)

    plot_npe = os.path.join(STATS_DIR, "Plot_NPE_greater_than_PE.png")
    plotting.plot_stat_map(z_map_npe_gt_pe, threshold=2.3, display_mode='z', 
                           cut_coords=[-10, 0, 10, 20, 30, 40],
                           title="NPE > PE (\u0394 rsFC, uncorrected Z > 2.3)",
                           output_file=plot_npe)

    print(f"\n--- ALL DONE! Check the {STATS_DIR} folder for your final maps. ---")

if __name__ == "__main__":
    run_group_statistics()
