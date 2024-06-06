#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import pandas as pd
import yaml
import os
import logging
from Weight import CorsikaWeight
import h5py
from PlotHelper import PlotHelper

logger = logging.getLogger(__name__)


class Stack():
    def __init__(self, filepath, config_var):
        self.filepath = filepath
        self.config_var = config_var

    def hdf5Reader(self, dir):
        # Directory containing the HDF5 files
        directory = dir

        # Get list of HDF5 files in the directory
        hdf5_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.hdf5')]
        return hdf5_files
    
    def iniPad(self,var):
        plt.figure()
        plt.xlabel(var)
        # todo : remove this hardcode
        plt.ylabel("NEvents")
        
    def processHist(self,args):
        # load plot helper and the vars and colors for plotting
        plot_helper = PlotHelper()

        vars = plot_helper.loadVars()
        colors = plot_helper.loadColors()

        for var, color in zip(vars, colors):
            plt.figure()
            for hdf5_file in self.hdf5Reader(args.outdir):
                with h5py.File(hdf5_file, 'r') as f:
                    data = f[var][:]
                    bins, min_val, max_val = plot_helper.readConfigs(var, args)
                    if "CORSIKA" in hdf5_file:
                        weighter = CorsikaWeight()
                        weights = weighter.makeWeights(hdf5_file)
                        plt.hist(data, bins=bins, range=(min_val, max_val), color=color, alpha=0.5, label=plot_helper.parseLegend(hdf5_file), weight = weights)
                    else: 
                        plt.hist(data, bins=bins, range=(min_val, max_val), color=color, alpha=0.5, label=plot_helper.parseLegend(hdf5_file))
                plt.legend(fontsize=6)
                plt.show()
                plt.savefig(self.filepath+'/plots/'+var)
            

if __name__ == "__main__":
    stack = Stack()
    stack.plot()
