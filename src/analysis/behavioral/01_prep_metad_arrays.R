# Title: Data Preprocessing for Metacognitive Efficiency Analysis
# Project: pe-decnef-kim2026
# Authors: Soan Kim
# Purpose: We filter test-phase data and calculate 4-AFC adjusted d-prime with padded confidence distribution arrays for MLE optimization.

Exp <- read.csv('~/[put dir here]/test.csv')
Exp$group <- as.factor(Exp$group)
num_cols <- c('block', 'choice', 'odd', 'accuracy', 'RT', 'confidence', 'confidenceRT', 'ID', 'age', 'gender', 'IQ', 'classifier', 'RR', 'education', 'group', 'phase', 'day, item_num', 'trial_idx')
Exp$item_num <- as.factor(Exp$item_num*Exp$day)
Exp$day <- as.factor(Exp$day)
Exp$ID <- as.factor(Exp$ID)

Exp_correct <- Exp[which(Exp$phase=='test' & Exp$accuracy==1),]
Exp_incorrect <- Exp[which(Exp$phase=='test' & Exp$accuracy==0),]

Exp1 <- Exp[which(Exp$phase=='test' & Exp$day==1),]
Exp2 <- Exp[which(Exp$phase=='test' & Exp$day==2),]
Exp3 <- Exp[which(Exp$phase=='test' & Exp$day==3),]

Exp_two <- Exp[which(Exp$phase=='test' & Exp$day!=3),]
print(colnames(Exp))

PE <- Exp[which(Exp$group=='PE'),]
NP <- Exp[which(Exp$group=='NonPE'),]

meta_data <- Exp %>%
  dplyr::filter(phase == 'test') %>%
  tidyr::drop_na(accuracy, confidence, ID, group, day) %>%
  dplyr::mutate(confidence = as.numeric(as.character(confidence)))

array_data <- meta_data %>%
  dplyr::group_by(ID, group, day) %>%
  dplyr::summarise(
    err_4 = sum(accuracy == 0 & confidence == 4),
    err_3 = sum(accuracy == 0 & confidence == 3),
    err_2 = sum(accuracy == 0 & confidence == 2),
    err_1 = sum(accuracy == 0 & confidence == 1),
    corr_1 = sum(accuracy == 1 & confidence == 1),
    corr_2 = sum(accuracy == 1 & confidence == 2),
    corr_3 = sum(accuracy == 1 & confidence == 3),
    corr_4 = sum(accuracy == 1 & confidence == 4),
    hit_rate = mean(accuracy),
    .groups = 'drop'
  ) %>%
  dplyr::mutate(
    hit_rate = pmin(pmax(hit_rate, 0.01), 0.99),
    d_prime_4afc = qnorm(hit_rate) - qnorm(0.25)
  )

write.csv(array_data, "matlab_meta_d_input.csv", row.names = FALSE)
