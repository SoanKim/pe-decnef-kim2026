# !/usr/bin/env python
# -*- coding: utf-8 -*-

# Title: Unified Behavioral Analysis and Visualization
# Project: pe-decnef-kim2026
# Author: Soan Kim
# Purpose: Perform linear mixed-model (LMM) analysis on behavioral metrics and generate publication-ready figures and LaTeX results tables.

def generate_mratio_plot_and_table(matlab_csv_path):
    df = pd.read_csv(matlab_csv_path)
    df = df.dropna(subset=['m_ratio'])
    df = df[np.isfinite(df['m_ratio'])]

    df['group'] = df['group'].astype(str)
    df['day'] = df['day'].astype(int)

    try:
        model = smf.mixedlm("m_ratio ~ C(group, Treatment('NonPE')) * C(day, Treatment(1))", df, groups=df["ID"])
        res = model.fit()

        summary_table = res.summary().tables[1]
        out_df = pd.DataFrame(summary_table.data[1:], columns=summary_table.data[0])
        out_df.rename(columns={out_df.columns[0]: 'Effect'}, inplace=True)

        out_df['Effect'] = out_df['Effect'].str.replace("C(group, Treatment('NonPE'))[T.PE]", 'Group (PE)', regex=False)
        out_df['Effect'] = out_df['Effect'].str.replace("C(day, Treatment(1))[T.2]", 'Day 2', regex=False)
        out_df['Effect'] = out_df['Effect'].str.replace("C(day, Treatment(1))[T.3]", 'Day 3', regex=False)
        out_df['Effect'] = out_df['Effect'].str.replace(':', ' x ', regex=False)

        def format_p_val(p_str):
            try:
                p = float(p_str)
                return "< 0.001" if p < 0.001 else f"{p:.3f}"
            except:
                return p_str

        if 'P>|z|' in out_df.columns:
            out_df['P>|z|'] = out_df['P>|z|'].apply(format_p_val)

        final_df = out_df[['Effect', 'Coef.', 'Std.Err.', 'z', 'P>|z|']].copy()
        final_df.columns = ['Effect', 'Estimate', 'SE', '$z$', '$p$']

        latex_code = final_df.to_latex(index=False, escape=False)

        full_latex = (
            "\\begin{table}[htbp]\n\\centering\n"
            "\\caption{Linear Mixed-Effects Model Results for Metacognitive Efficiency (M-ratio)}\n"
            "\\label{tab:lmm_mratio_efficiency}\n"
            f"{latex_code}"
            "\\end{table}"
        )

        table_path = os.path.join(TABLE_DIR, "lmm_mratio_efficiency.tex")
        with open(table_path, "w") as f:
            f.write(full_latex)

        print("\n--- LMM LaTeX Table Generated ---")
        print(full_latex)
        print("---------------------------------\n")

    except Exception as e:
        print(f"LMM fit failed: {e}")

    plt.figure(figsize=(7, 6))
    ax = sns.lineplot(data=df, x='day', y='m_ratio', hue='group', style='group',
                      markers=True, dashes=False, err_style="bars",
                      palette={'PE': '#d62728', 'NonPE': '#7f7f7f'},
                      linewidth=2.5, markersize=9, err_kws={'capsize': 5, 'elinewidth': 1.5})

    plt.axhline(1.0, linestyle='--', color='gray', alpha=0.7)
    plt.title('Metacognitive Efficiency (M-ratio)', fontsize=16, weight='bold', pad=15)
    plt.ylabel("M-ratio (meta-d'/d')", fontsize=14)
    plt.xlabel('Test Session', fontsize=14)
    plt.xticks([1, 2, 3], ['Pre', 'Interim', 'Post'])

    handles, labels = ax.get_legend_handles_labels()
    clean_labels = ['PE Group' if l == 'PE' else 'Non-PE Group' if l == 'NonPE' else l for l in labels]
    plt.legend(handles=handles, labels=clean_labels, frameon=True, edgecolor='gray')

    sns.despine()
    plt.tight_layout()
    plot_path = os.path.join(PLOT_DIR, "behavior_mratio_efficiency.png")
    plt.savefig(plot_path, dpi=300)
    print(f"Plot saved to: {plot_path}")
