rm(list = ls()) 

#Libraries----------------------------------------------------------------------
library(ppcor)
library(tidyverse)
library(ggplot2)
library(cowplot)
library(ggpubr)
library(reshape2)
library(panelr)


###################################### Tau data ###################################################
dbsi_data <- read.csv('Desktop/CS1P1_ADRD/Grant_analysis/cs1p1_OC_YC_dbsi_FS_regions.csv', header = TRUE)
dbsi_data <- dbsi_data[dbsi_data$DBSI_Scan == c('hind_ratio_map_to_t1'), ]
dbsi_data <- dbsi_data[dbsi_data$ROI %in% c("ctx_lh_entorhinal", "ctx_rh_entorhinal",
                                           "Left_Amygdala", "Right_Amygdala",
                                           "ctx_lh_inferiortemporal", "ctx_rh_inferiortemporal",
                                           "ctx_lh_lateraloccipital", "ctx_rh_lateraloccipital"), ]

data_lh <- dplyr::filter(dbsi_data, grepl('ctx_lh|Left', ROI))
data_rh <- dplyr::filter(dbsi_data, grepl('ctx_rh|Right', ROI))


data_lh$Value_rh <- data_rh$Value
data_lh$NVoxels_rh <- data_rh$NVoxels
colnames(data_lh)[5] <- "Value_lh"
colnames(data_lh)[6] <- "NVoxels_lh"

data_lh <- data_lh %>% 
  mutate(Value_mean = (Value_lh*NVoxels_lh + Value_rh*NVoxels_rh)/(NVoxels_lh+NVoxels_rh))

data_lh$ROI <- gsub("Left_", "", data_lh$ROI)
data_lh$ROI <- gsub("_lh_", "_", data_lh$ROI)

write.csv(data_lh, 'Desktop/CS1P1_ADRD/Grant_analysis/Final_LR_weighted/cs1p1_OC_YC_tau_individual.csv', row.names=FALSE)

data <- data_lh %>% 
  group_by(Session,Condition) %>%
  summarize(Value=mean(Value_mean))

data <- data %>% 
  mutate(ROI = "Tau_regions")
tau_data <- data[,c(1,2,4,3)]

###################################### Hippocampus data ###################################################
dbsi_data <- read.csv('Desktop/CS1P1_ADRD/Grant_analysis/cs1p1_OC_YC_dbsi_FS_regions.csv', header = TRUE)
dbsi_data <- dbsi_data[dbsi_data$DBSI_Scan == c('hind_ratio_map_to_t1'), ]
dbsi_data <- dbsi_data[dbsi_data$ROI %in% c("Left_Hippocampus", "Right_Hippocampus"), ]

data_lh <- dplyr::filter(dbsi_data, grepl('ctx_lh|Left', ROI))
data_rh <- dplyr::filter(dbsi_data, grepl('ctx_rh|Right', ROI))


data_lh$Value_rh <- data_rh$Value
data_lh$NVoxels_rh <- data_rh$NVoxels
colnames(data_lh)[5] <- "Value_lh"
colnames(data_lh)[6] <- "NVoxels_lh"

data_lh <- data_lh %>% 
  mutate(Value_mean = (Value_lh*NVoxels_lh + Value_rh*NVoxels_rh)/(NVoxels_lh+NVoxels_rh))
data_lh$ROI <- gsub("Left_", "", data_lh$ROI)

write.csv(data_lh, 'Desktop/CS1P1_ADRD/Grant_analysis/Final_LR_weighted/cs1p1_OC_YC_hippocampus_individual.csv', row.names=FALSE)

data <- data_lh %>% 
  group_by(Session, Condition) %>%
  summarize(Value=mean(Value_mean))

data <- data %>% 
  mutate(ROI = "Hippocampus")
hippocmp_data <- data[,c(1,2,4,3)]

###################################### Amyloid data ###################################################
dbsi_data <- read.csv('Desktop/CS1P1_ADRD/Grant_analysis/cs1p1_OC_YC_dbsi_FS_regions.csv', header = TRUE)
dbsi_data <- dbsi_data[dbsi_data$DBSI_Scan == c('hind_ratio_map_to_t1'), ]
dbsi_data <- dbsi_data[dbsi_data$ROI %in% c("ctx_lh_precuneus", "ctx_rh_precuneus",
                                            "ctx_lh_superiorfrontal", "ctx_rh_superiorfrontal",
                                            "ctx_lh_rostralmiddlefrontal", "ctx_rh_rostralmiddlefrontal",
                                            "ctx_lh_lateralorbitofrontal", "ctx_rh_lateralorbitofrontal", 
                                            "ctx_lh_medialorbitofrontal", "ctx_rh_medialorbitofrontal",
                                            "ctx_lh_superiortemporal", "ctx_rh_superiortemporal", 
                                            "ctx_lh_middletemporal", "ctx_rh_middletemporal") , ]

data_lh <- dplyr::filter(dbsi_data, grepl('ctx_lh|Left', ROI))
data_rh <- dplyr::filter(dbsi_data, grepl('ctx_rh|Right', ROI))


data_lh$Value_rh <- data_rh$Value
data_lh$NVoxels_rh <- data_rh$NVoxels
colnames(data_lh)[5] <- "Value_lh"
colnames(data_lh)[6] <- "NVoxels_lh"

data_lh <- data_lh %>% 
  mutate(Value_mean = (Value_lh*NVoxels_lh + Value_rh*NVoxels_rh)/(NVoxels_lh+NVoxels_rh))

data_lh$ROI <- gsub("_lh_", "_", data_lh$ROI)

write.csv(data_lh, 'Desktop/CS1P1_ADRD/Grant_analysis/Final_LR_weighted/cs1p1_OC_YC_amyloid_individual.csv', row.names=FALSE)

data <- data_lh %>% 
  group_by(Session, Condition) %>%
  summarize(Value=mean(Value_mean))

data <- data %>% 
  mutate(ROI = "Amyloid_regions")
amyloid_data <- data[,c(1,2,4,3)]


summary_region <- rbind(amyloid_data, hippocmp_data, tau_data)
write.csv(summary_region, 'Desktop/CS1P1_ADRD/Grant_analysis/Final_LR_weighted/cs1p1_OC_YC_summary_regions_averaged.csv', row.names=FALSE)

summary_region$Condition <- factor(summary_region$Condition,levels = c("Young_control", "Old_control"))

p_hind <- ggplot(data = summary_region, aes(x = ROI, y = Value, color = Condition, fill="gray95")) +
  geom_boxplot(outlier.color = "black", outlier.shape = 17, outlier.size = 2) +
  scale_color_manual(values=c("Young_control"="blue", "Old_control"="red")) +
  scale_fill_manual(values=c("gray95")) +
  scale_x_discrete(labels=c("Amyloid regions", "Tau regions", "Hippocampus")) +
  labs(x = NULL, y = "Hindered Ratio") +
  guides(fill = FALSE, color=guide_legend(title=NULL)) +
  theme_bw() +
  theme(axis.text.x = element_text(angle=0, size=12, color = "black"),
        axis.text.y = element_text(size=12),
        axis.title = element_text(size = 18, vjust=1),
        legend.text = element_text(size=11),
        legend.position = c(0.82,0.90),
        panel.border = element_rect(color='black'),
        panel.grid.major = element_blank())
p_hind



ggsave("Desktop/CS1P1_ADRD/Grant_analysis/Final_NW/HR_YC_OC_summary_regions_noweight.jpg", p_hind,
       width = 24, height = 20, units = c("cm"), dpi = 300)