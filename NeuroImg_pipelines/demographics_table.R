library(gtsummary)
library(tidyverse)
library(finalfit)
library(dplyr)

# Method 1 : Use gtsummary library package to generate demographics summary

pr_data <- read.csv('./Demographics_pr.csv', header = TRUE)
pr_data$condition <- factor(pr_data$condition,levels = c("CON", "BP", "SCZ"))
pr_data$BMI.factor <- factor(pr_data$BMI.factor,levels = c("Underweight", "Healthy", "Overweight", "Obese"))
pr_data$Anti_Psychotic.factor <- factor(pr_data$Anti_Psychotic.factor,
                                        levels = c("Typical", "Atypical", "None"),
                                        labels = c("Typical neuroleptics", "Atypical neuroleptics", "None"))
pr_data$Mood_Stabilizer.factor <- factor(pr_data$Mood_Stabilizer.factor,
                                         levels = c("Lithium", "Anti-convulsant", "Both", "None"))
pr_data$Anti_Depressant.factor <- factor(pr_data$Anti_Depressant.factor,
                                         levels = c("SSRI/SNRI", "Atypical", "Both", "None"))
pr_data$Other.No.medication.factor <- factor(pr_data$Other.No.medication.factor,
                                             levels = c("Other", "None", "Included"))


# Change label names using ff_label
pr_data <- pr_data %>%
  mutate(
    age = ff_label(age, "Age"),
    gender.factor = ff_label(gender.factor, "Gender"),
    BMI.factor = ff_label(BMI.factor, "BMI Group"),
    Anti_Psychotic.factor = ff_label(Anti_Psychotic.factor, "Anti Psychotic medications"),
    Mood_Stabilizer.factor = ff_label(Mood_Stabilizer.factor, "Mood Stabilizers"),
    Anti_Depressant.factor = ff_label(Anti_Depressant.factor, "Anti Depressants"),
    Other.No.medication.factor = ff_label(Other.No.medication.factor, "Other/No medications")
  )

summary <- pr_data %>% select(c(condition,age,gender.factor,BMI, BMI.factor, Anti_Psychotic.factor, Mood_Stabilizer.factor, Anti_Depressant.factor, Other.No.medication.factor)) %>%
  tbl_summary(by = condition,
              digits = list(all_continuous() ~ c(2, 1),
                            all_categorical() ~ c(0, 1)),
              statistic = list(
                all_continuous() ~ "{mean} ({sd})",
                all_categorical() ~ "{n} ({p}%)"),
              missing = "no",
              ) %>%
  add_p(include = c(age, gender.factor, BMI))

summary <- remove_row_type(
  summary,
  variables = c(Anti_Psychotic.factor, Mood_Stabilizer.factor, Anti_Depressant.factor),
  type = c("level"),
  level_value = c("None")
)

summary <- remove_row_type(
  summary,
  variables = c(Other.No.medication.factor),
  type = c("level"),
  level_value = c("Included")
)

summary
gtsave(glue("Desktop/Draft_docs/summary.png"))
save(summary, "Desktop/Draft_docs/summary.png")


###
# Method 2 : Use finalfit library package to generate demographics summary 
# explanatory <- c("age", "gender.factor", "BMI", "BMI.factor")
# dependent <- c("condition")
# 
# pr_data %>%
#   summary_factorlist(dependent, explanatory, 
#                      add_dependent_label=FALSE,
#                      digits = c(2)) -> t1
# knitr::kable(t1, row.names=FALSE, align=c("r", "r", "r", "r", "r"))
# t1
