#!/usr/bin/env python
# -*- coding: utf-8 -*-
# FIle name: plot_induction_trajectories.py
# It creates a final multi-panel figure, combining the voxel-wise $t$-statistic brain maps with the behavioral boxplots.

import os
import sys
import numpy as np
import nibabel as nib
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.ndimage import label
from nilearn import plotting
import matplotlib.gridspec as gridspec
from matplotlib.colorbar import ColorbarBase
from matplotlib.colors import Normalize

PARTICIPANTS_DIR = "/[put path here]/participants"
CSV_PATH = "Master_Induction_Plotting_Data.csv"
OUTPUT_DIR = "plots"
OUTPUT_FIG = os.path.join(OUTPUT_DIR, "decnef_induction_figure.png")

os.makedirs(OUTPUT_DIR, exist_ok=True)

PE_IDS = [6, 14, 18, 24, 25, 26, 35, 38, 39, 40, 42, 43, 47, 54]
NPE_IDS = [5, 9, 15, 17, 22, 27, 28, 29, 41, 46, 48, 50, 51, 53]
ALL_IDS = PE_IDS + NPE_IDS

CLUSTER_SIZE = 100 
T_THRESH = 2.05    

def check_paths():
    if not os.path.exists(PARTICIPANTS_DIR):
        print(f"PARTICIPANTS_DIR not found at: {PARTICIPANTS_DIR}")
        sys.exit(1)
    if not os.path.exists(CSV_PATH):
        print(f"CSV file not found at: {CSV_PATH}. Boxplot will be skipped.")

def add_stat_annotation(ax, data, condition, i):
    subset = data[data['Condition'] == condition]
    g1 = subset[subset['Group'] == 'PE']['Logit']
    g2 = subset[subset['Group'] == 'Non-PE']['Logit']

    if len(g1) < 2 or len(g2) < 2: return
    _, p_val = stats.ttest_ind(g1, g2, equal_var=False)

    current_max = subset['Logit'].max()
    y_pos = current_max + 0.1 
    
    if p_val < 0.05 or (p_val < 0.10 and condition == 'Session 2'):
        if p_val < 0.001: star, fs = "***", 18
        elif p_val < 0.01: star, fs = "**", 18
        elif p_val < 0.05: star, fs = "*", 18
        else: star, fs = "†", 14
        
        x1, x2 = i - 0.2, i + 0.2
        ax.plot([x1, x1, x2, x2], [y_pos, y_pos + 0.02, y_pos + 0.02, y_pos], lw=1.2, c='k')
        ax.text((x1 + x2) / 2, y_pos + 0.02, star, ha='center', va='bottom', fontsize=fs)

def create_strict_intersection_mask():
    print("Step 1: Calculating Mask...")
    common_mask = None
    files_found = 0
    
    for sid in ALL_IDS:
        p = os.path.join(PARTICIPANTS_DIR, "decoder_searchlight/AUCmaps", f"subject-{sid}_searchlight_AUC_LOGO_Corrected_MNI.nii.gz")
        if os.path.exists(p):
            files_found += 1
            img_data = nib.load(p).get_fdata()
            voxel_mask = (np.abs(img_data) > 1e-5) & (~np.isnan(img_data))
            common_mask = voxel_mask if common_mask is None else np.logical_and(common_mask, voxel_mask)
    
    if common_mask is None:
        print("ERROR: No files were loaded. Cannot create mask.")
        sys.exit(1)
    return common_mask

def plot_full_timeline(shrunk_mask):
    print("Step 2: Generating Figure...")
    fig = plt.figure(figsize=(22, 12), facecolor='white')
    gs = gridspec.GridSpec(2, 4, height_ratios=[1.1, 1], hspace=0.3, wspace=0.1)
    
    sessions = [('Decoder', 0), ('NF S1', 1), ('NF S2', 2), ('NF S3', 3)]
    affine = None
    all_t_stats = []

    try:
        cmap_obj = plt.get_cmap('cold_hot')
    except:
        cmap_obj = plt.get_cmap('RdBu_r') 

    for i, (label_text, s_idx) in enumerate(sessions):
        print(f"  Processing {label_text}...")
        pe_vols, npe_vols = [], []
        
        for sid in PE_IDS:
            if s_idx == 0: p = os.path.join(PARTICIPANTS_DIR, "decoder_searchlight/AUCmaps", f"subject-{sid}_searchlight_AUC_LOGO_Corrected_MNI.nii.gz")
            elif sid == 35 and s_idx == 3: p = os.path.join(PARTICIPANTS_DIR, f"subject-35/decoding_dice2decnef/searchlight_hitrate/dice2decnef_searchlight_results_logistic_probs_radius_4_session-3_MNI_2mm_MASKED.nii.gz")
            else: p = os.path.join(PARTICIPANTS_DIR, f"subject-{sid}/decoding_dice2decnef/MNI_induction_sessions/dice2decnef_searchlight_results_logistic_probs_radius_4_session-{s_idx}_MNI_2mm.nii.gz")
            if os.path.exists(p):
                img = nib.load(p); pe_vols.append(img.get_fdata())
                if affine is None: affine = img.affine
        
        for sid in NPE_IDS:
            if s_idx == 0: p = os.path.join(PARTICIPANTS_DIR, "decoder_searchlight/AUCmaps", f"subject-{sid}_searchlight_AUC_LOGO_Corrected_MNI.nii.gz")
            else: p = os.path.join(PARTICIPANTS_DIR, f"subject-{sid}/decoding_dice2decnef/MNI_induction_sessions", f"dice2decnef_searchlight_results_logistic_probs_radius_4_session-{s_idx}_MNI_2mm.nii.gz")
            if os.path.exists(p): npe_vols.append(nib.load(p).get_fdata())

        if len(pe_vols) > 0 and len(npe_vols) > 0:
            t_stat, _ = stats.ttest_ind(np.array(pe_vols), np.array(npe_vols), axis=0, nan_policy='omit')
            t_stat[~shrunk_mask] = 0
            t_stat = np.nan_to_num(t_stat)
            lab, n = label(np.abs(t_stat) > T_THRESH)
            for c in range(1, n+1):
                if np.sum(lab == c) < CLUSTER_SIZE: t_stat[lab == c] = 0
            all_t_stats.append(t_stat)
        else:
            all_t_stats.append(np.zeros_like(shrunk_mask, dtype=float))

        ax_brain = fig.add_subplot(gs[0, i])
        plotting.plot_stat_map(nib.Nifti1Image(all_t_stats[-1], affine), display_mode='z', cut_coords=[25], 
                               threshold=T_THRESH, vmax=5, axes=ax_brain, colorbar=False, annotate=False, 
                               draw_cross=False, cmap=cmap_obj, title=label_text)

    cbar_ax = fig.add_axes([0.92, 0.65, 0.015, 0.2]) 
    cb = ColorbarBase(cbar_ax, cmap=cmap_obj, norm=Normalize(vmin=-5, vmax=5), orientation='vertical')
    cbar_ax.set_title("T-Statistic\n(PE > Non-PE)", fontsize=12, fontweight='bold', pad=15)

    ax_plot = fig.add_subplot(gs[1, 1:3]) 
    if os.path.exists(CSV_PATH):
        print("  Processing Behavioral Plot...")
        df = pd.read_csv(CSV_PATH)
        order = ['Day 2 (Decoder)', 'Session 1', 'Session 2', 'Session 3']
        
        plot_df = df[df['Condition'].isin(order)].copy()
        plot_df['Condition'] = pd.Categorical(plot_df['Condition'], categories=order, ordered=True)

        ax_plot.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        sns.boxplot(data=plot_df, x='Condition', y='Logit', hue='Group', 
                    palette={'PE': '#666666', 'Non-PE': '#FFFFFF'},
                    width=0.5, showfliers=False, ax=ax_plot, 
                    boxprops=dict(alpha=0.8, edgecolor='k'), medianprops=dict(color='k'))
        sns.stripplot(data=plot_df, x='Condition', y='Logit', hue='Group', dodge=True, jitter=True,
                      palette={'PE': 'black', 'Non-PE': 'gray'}, size=4, alpha=0.6, ax=ax_plot)

        new_labels = ['Decoder', 'Neurofeedback\nSession 1', 'Neurofeedback\nSession 2', 'Neurofeedback\nSession 3']
        ax_plot.set_xticklabels(new_labels, fontsize=11)
        
        for i, cond in enumerate(order):
            add_stat_annotation(ax_plot, plot_df, cond, i)

        ax_plot.set_ylabel("Induction Magnitude (Logits)", fontsize=12)
        ax_plot.set_xlabel("")
        handles, labels = ax_plot.get_legend_handles_labels()
        ax_plot.legend(handles[0:2], ['PE Group', 'Non-PE Group'], title=None, 
                       loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2, fontsize=10, frameon=False)
        sns.despine(ax=ax_plot)

    fig.suptitle("Neurofeedback Induction of Prediction Error", fontsize=20, weight='bold', y=0.95)
    plt.savefig(OUTPUT_FIG, dpi=300, bbox_inches='tight')
    print(f"\nSUCCESS: Figure saved to {OUTPUT_FIG}")

if __name__ == "__main__":
    check_paths()
    mask = create_strict_intersection_mask()
    plot_full_timeline(mask)
