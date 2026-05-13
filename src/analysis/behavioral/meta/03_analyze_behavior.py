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

    model = smf.mixedlm("m_ratio ~ C(group, Treatment('NonPE')) * C(day, Treatment(1))",
                        df, groups=df["ID"])
    res = model.fit()

    df_res = pd.DataFrame(res.summary().tables[1])
    df_res.columns = df_res.iloc[0]
    df_res = df_res.drop(df_res.index[0]).reset_index()
    df_res.columns = ['Effect', 'Estimate', 'SE', 'z', 'p', '[0.025', '0.975]']

    df_res['Effect'] = df_res['Effect'].str.replace("C(group, Treatment('NonPE'))[T.PE]", 'Group (PE)', regex=False)
    df_res['Effect'] = df_res['Effect'].str.replace("C(day, Treatment(1))[T.2]", 'Day 2', regex=False)
    df_res['Effect'] = df_res['Effect'].str.replace("C(day, Treatment(1))[T.3]", 'Day 3', regex=False)
    df_res['Effect'] = df_res['Effect'].str.replace(':', ' x ', regex=False)

    def format_p(p_val):
        try:
            p = float(p_val)
            return "< 0.001" if p < 0.001 else f"{p:.3f}"
        except:
            return str(p_val)

    df_res['p'] = df_res['p'].apply(format_p)

    final_df = df_res[['Effect', 'Estimate', 'SE', 'z', 'p']].copy()
    final_df.columns = ['Effect', 'Estimate', 'SE', '$z$', '$p$']

    latex_body = final_df.to_latex(index=False, escape=False)
    full_latex = (
        "\\begin{table}[htbp]\n\\centering\n"
        "\\caption{Linear Mixed-Effects Model Results for Metacognitive Efficiency (M-ratio)}\n"
        "\\label{tab:lmm_mratio_efficiency}\n"
        f"{latex_body}"
        "\\end{table}"
    )

    os.makedirs(TABLE_DIR, exist_ok=True)
    table_path = os.path.join(TABLE_DIR, "lmm_mratio_efficiency.tex")
    with open(table_path, "w") as f:
        f.write(full_latex)

    print(f"\n[SUCCESS] LaTeX table saved to: {os.path.abspath(table_path)}")

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
    plt.legend(handles=handles, labels=['PE Group', 'Non-PE Group'], frameon=True, edgecolor='gray')

    sns.despine()
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "behavior_mratio_efficiency.png"), dpi=300)
    print(f"[SUCCESS] Plot saved to: {os.path.join(PLOT_DIR, 'behavior_mratio_efficiency.png')}")
