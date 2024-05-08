#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import yaml
import os
import logging

class Stack():
    def __init__(self, histpath, config_var):
        self.histpath = histpath
        self.config_var = config_var

    def csvUnpack(self, histfile):
        df = pd.read_csv(histfile, index_col=0)
        return df
    
    def iniPad(self,var):
        plt.figure()
        plt.xlabel(var)
        plt.ylabel("NEvents")
        return plt
    
    def processHist(self):
        with open(self.config_var, 'r') as f:
            d_histVars = yaml.full_load(f)
            for var,bins in d_histVars.items():
                # make plot
                plt = self.iniPad(var)
                for histfile in os.listdir(self.histpath):
                    histfile = os.path.join(self.histpath, histfile)
                    df = self.csvUnpack(histfile=histfile)
                    hist_info = df[var]
                    hist = hist_info.iloc[6:]
                    plt.bar(hist, hist.index)
                    plt.savefig(self.histpath+'plots')
                    # plt.hist(hist_info.iloc[:7])
                    # plt.hist(hist_info.iloc[:7],bins=bins[0],range=bins[:2], color = hist_info.loc['color'], legend = hist_info.loc['legend'])
            

if __name__ == "__main__":
    stack = Stack()
    stack.plot()
