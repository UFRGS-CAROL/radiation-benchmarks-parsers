#!/usr/bin/env Rscript

library(ggplot2)
library(scales)
args = commandArgs(trailingOnly=TRUE)

if (length(args)<2) {
  stop("At least two argument must be supplied, input file and outputfile", call.=FALSE)
}

dat = read.csv(args[1],sep=",")

pdf(file = args[2])
#ggplot(dat, aes(x=errLimit, y=percentage, colour=benchmark)) +
ggplot(dat, aes(x=Threshold, y=Percentage, group=Device), method = "lm", formula = y ~ poly(x, 10)) +
ylim(0,100)+
geom_line(aes(linetype=Device, colour=Device), size=1.1) +
scale_linetype_manual(values=c("solid", "dotdash", "solid", "solid", "solid", "dotdash")) +
scale_color_manual(values=c('#3465A4','#3465A4', '#FF950E', '#336600', '#231111', '#332200'))+
labs(x = "Tolerated Relative Error [%]", y = "GEMM FIT rate [%]", group="Device") +
theme(legend.position="bottom",axis.text.x=element_text(size=14) , axis.text.y=element_text(size=14) , text = element_text(size = 14)) 

dev.off()
