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
        
    def processHist(self, args):
        # load plot helper and the vars and colors for plotting
        plot_helper = PlotHelper(config_var=self.config_var)

        vars = plot_helper.loadVars()
        colors = plot_helper.loadColors()

        for var in vars:
            logger.info("Plotting variable: %s", var)
            plt.figure()
            for hdf5_file_path, color in zip(self.hdf5Reader(args.outdir), colors):
                logger.debug(f"Variable: {var}")
                bins, min_val, max_val = plot_helper.readConfigs(var, args)
                
                # Ensure bins, min_val, and max_val are of type float
                bins = int(bins)
                min_val = int(min_val)
                max_val = int(max_val)

                # Open the HDF5 file
                with h5py.File(hdf5_file_path, 'r') as hdf5_file:
                    # Directly access the dataset and ensure it's a float array
                    data = np.asarray(hdf5_file[var]['value'][:], dtype=float)
                    if "CORSIKA" in hdf5_file_path:
                        corsikaweight = CorsikaWeight()
                        weights = corsikaweight.makeWeights(hdf5_file_path)                        
                        logger.info(f"Currently plotting CORSIKA")
                        plt.hist(data, bins=bins, range=(min_val, max_val), color=color, alpha=0.3, label="CORSIKA", weights=weights)
                    else: 
                        legend = ' '.join((hdf5_file_path.split('/')[-1]).replace('.', ' ').replace('_', ' ').replace('-', ' ').split()[:-4])
                        logger.info(f"Currently plotting sample: {legend}")   
                        plt.hist(data, bins=bins, range=(min_val, max_val), color=color, alpha=0.5, label=legend)   
                        print('beep')

            plt.legend(fontsize=6)
            plt.show()
            if not os.path.exists(self.filepath+'plots'):
                os.makedirs(self.filepath+'plots')
            plt.savefig(self.filepath+'plots/'+var)
            

if __name__ == "__main__":
    stack = Stack()
    stack.plot()
