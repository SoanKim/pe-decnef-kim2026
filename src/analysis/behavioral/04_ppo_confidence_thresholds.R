# Title: Partial Proportional Odds (PPO) Modeling of Confidence
# Project: pe-decnef-kim2026
# Author: Kim et al.
# Purpose: Test the parallel slopes assumption for ordinal confidence data and estimate threshold-specific log-odds to identify group-level bias shifts.

if (!dir.exists("tables")) dir.create("tables")
if (!dir.exists("[put dir here]")) dir.create("[put dir here]")

Exp_clean <- na.omit(Exp[Exp$phase == 'test', c("confidence", "group", "day", "ID")])
Exp_clean$confidence <- ordered(Exp_clean$confidence)

ppo_model <- clmm2(confidence ~ day, 
                   nominal = ~ group, 
                   random = ID, 
                   data = Exp_clean, 
                   Hess = TRUE, 
                   nAGQ = 10)

est <- ppo_model$coefficients
se  <- sqrt(diag(solve(ppo_model$Hessian)))
z_val <- est / se
p_val <- 2 * (1 - pnorm(abs(z_val)))

results_df <- data.frame(
  Estimate = est,
  StdErr = se,
  Z = z_val,
  P = p_val
)

stargazer(results_df, 
          type = "latex", 
          summary = FALSE, 
          title = "PPO Model: Threshold-Specific Logic Coefficients",
          out = "tables/ppo_confidence_results.tex",
          label = "tab:ppo_results")

group_terms <- c("1|2.groupPE", "2|3.groupPE", "3|4.groupPE")
plot_data <- results_df[rownames(results_df) %in% group_terms, ]
plot_data$Threshold <- c(">1", ">2", ">3")
plot_data$Stars <- ifelse(plot_data$P < 0.05, "*", "")

ggplot(plot_data, aes(x = Threshold, y = Estimate)) +
  geom_point(size = 4, color = "#d62728") +
  geom_errorbar(aes(ymin = Estimate - 1.96 * StdErr, ymax = Estimate + 1.96 * StdErr), 
                width = 0.1, color = "black", linewidth = 1.0) +
  geom_text(aes(label = Stars, y = Estimate + 1.96 * StdErr + 0.05), 
            size = 9, vjust = 0, fontface = "bold") +
  geom_hline(yintercept = 0, linetype = "dashed", color = "gray50") +
  labs(title = "Group Effect Magnitude by Threshold",
       subtitle = "Significant divergence at absolute certainty (>3)",
       x = "Confidence Threshold",
       y = "Log-Odds (PE vs Non-PE)") +
  theme_minimal()

ggsave("[put dir here]/PPO_Threshold_Significance.png", width = 6, height = 5, dpi = 300)
