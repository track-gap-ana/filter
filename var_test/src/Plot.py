#!/usr/bin/env python
import glob
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import yaml
import re
import logging
import h5py
import os

class Stack():
    def __init__(self, histpath, config_var):
        self.histpath = histpath
        self.config_var = config_var

    def csvUnpack(self, histfile):
        df = pd.DataFrame.from_csv(histfile)
        return df
    
    def iniPad(self,var):
        plt.figure()
        for name, binInfo in var:
            plt.xlabel(var[name])
            plt.ylabel("NEvents")
        return plt
    
    def processHist(self):
        with open(self.config_var, 'r') as f:
            d_histVars = yaml.full_load(f)
            for var, bins in d_histVars:
                # make plot
                plt = self.iniPad(var, bins)
                for histfile in self.histpath:
                    df = self.csvUnpack(histfile=histfile)
                    hist_info = df[var]
                    plt.hist(hist_info.iloc[:7],bins=bins[0],range=bins[:2], color = hist_info.loc['color'], legend = hist_info.loc['legend'])
            

if __name__ == "__main__":
    stack = Stack()
    stack.plot()
