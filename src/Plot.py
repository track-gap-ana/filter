#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import yaml
import os
import logging

logging.basicConfig(level=logging.DEBUG)


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
        
    
    def processHist(self):
        with open(self.config_var, 'r') as f:
            d_histVars = yaml.full_load(f)
            for var,bins in d_histVars.items():
                logging.info('Plotting'+var)
                # make plot
                self.iniPad(var)
                print('histpath', self.histpath)
                for histfile in os.listdir(self.histpath):
                    histfile = os.path.join(self.histpath, histfile)
                    if os.path.isdir(histfile) == False:
                        print('histfile', histfile)
                        df = self.csvUnpack(histfile=histfile)
                        hist_info = df[var]
                        hist = hist_info.iloc[6:].astype(float)
                        print("range: ", tuple(bins[-2:]))
                        print('bins', bins[0])
                        print("color: ", hist_info.loc['color'])
                        print("legend name: ", hist_info.loc['legend'])
                        plt.hist(hist,bins=bins[0],range=tuple(bins[-2:]), color = hist_info.loc['color'], label = hist_info.loc['legend'], alpha=.5)
                plt.legend(fontsize=6)
                plt.savefig(self.histpath+'/plots/'+var)
            

if __name__ == "__main__":
    stack = Stack()
    stack.plot()
