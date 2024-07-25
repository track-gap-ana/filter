#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np
import os
import logging
from Weight import CorsikaWeight
import h5py
# --- 
import ConfigHelper

logger = logging.getLogger(__name__)


class Stack():
    def __init__(self, filepath, config_var, config_samples):
        self.config=ConfigHelper.ConfigHelper(config_var=config_var, config_samples=config_samples)

        self.vars = self.config.loadVars()
        self.colors = self.config.loadColors()
        self.filepath = self.config.makeDirs(filepath)
        self.sig_types = self.config.loadSigType()

    def hdf5Reader(self, dir):
        # Directory containing the HDF5 files
        directory = dir

        # Get list of HDF5 files in the directory

        hdf5_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.hdf5') and any(item.replace("*","") in f for item in self.sig_types)]
        logger.debug(f"Found HDF5 files: {hdf5_files}")
        return hdf5_files
    
    def iniPad(self,var):
        plt.figure()
        plt.xlabel(var)
        # todo : remove this hardcode
        plt.ylabel("NEvents")
        
    def processHist(self, args):

        for var in self.vars:
            logger.info("Plotting variable: %s", var)
            plt.figure()
            
            for hdf5_file_path, color in zip(self.hdf5Reader(self.filepath), self.colors):
                logger.debug(f"Variable: {var}")
                bins, min_val, max_val = self.config.readConfigs(var, args)
                
                # Ensure bins, min_val, and max_val are of type float
                bins = int(bins)
                min_val = int(min_val)
                max_val = int(max_val)

                # Open the HDF5 file
                with h5py.File(hdf5_file_path, 'r') as hdf5_file:
                    # Directly access the dataset and ensure it's a float array
                    logger.debug(f"Reading file: {hdf5_file}")
                    logger.debug(f"Available keys: {hdf5_file.keys()}")
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

            plt.legend(fontsize=6)
            plt.show()
            self.plotspath = self.config.makeDirs(os.path.join(self.filepath, "plots"))
            plt.savefig(self.plotspath+"/"+var+".png")
            

if __name__ == "__main__":
    stack = Stack()
    stack.plot()
