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
logging.getLogger('matplotlib').setLevel(logging.WARNING)

class Stack():
    def __init__(self, outdir, config_var, config_samples):
        self.config=ConfigHelper.ConfigHelper(config_var=config_var, config_samples=config_samples)

        self.vars = self.config.loadVars()
        self.colors = self.config.loadColors()
        self.outdir = self.config.makeDirs(outdir)
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
    
    def getLegend(self, file_path):
        legend = ' '.join((file_path.split('/')[-1]).replace('.', ' ').replace('_', ' ').replace('-', ' ').split()[:-4])
        if "noFilter" in file_path:
            legend += " No Filter"
        return legend
    
    def identifyPairs(self, hdf5_files):
        pairs = []
        for file in hdf5_files:
            if 'noFilter' in file:
                base_name = file.replace('_noFilter', '')
                for other_file in hdf5_files:
                    if other_file == base_name:
                        pairs.append((os.path.join(self.outdir, file), os.path.join(self.outdir, other_file)))
        return pairs

    def createSubplots(self, vars):
        fig, axes = plt.subplots(nrows=len(vars), ncols=1, figsize=(10, 5 * len(vars)))
        return fig, axes

    def plotHistogram(self, file_path, var, ax, bins, min_val, max_val, color, alpha):
        with h5py.File(file_path, 'r') as hdf5_file:
            data = np.asarray(hdf5_file[var]['value'][:], dtype=float)
            logger.debug(f"Reading file: {file_path}\n Histogram related: {data}")
            if "CORSIKA" in file_path:
                corsikaweight = CorsikaWeight()
                weights = corsikaweight.makeWeights(file_path)
                ax.hist(data, histtype='step', bins=bins, range=(min_val, max_val), color=color, alpha=alpha, label="CORSIKA", weights=weights)
            else:
                legend = self.getLegend(file_path)
                ax.hist(data, histtype='step', bins=bins, range=(min_val, max_val), color=color, alpha=alpha, label=legend)

    def saveFigure(self, fig, var):
        self.plotspath = self.config.makeDirs(os.path.join(self.outdir, "plots"))
        figpath = os.path.join(self.plotspath, f"{var}.png")
        plt.savefig(figpath)
        logger.debug(f"Saved figure: {figpath}")
        plt.close(fig)
        
    def onePlot(self, args):
        for var in self.vars:
            logger.info("Plotting variable: %s", var)
            self.iniPad(var)
            
            for hdf5_file_path, color in zip(self.hdf5Reader(self.outdir), self.colors):
                logger.debug(f"Variable: {var}")
                bins, min_val, max_val = self.config.readConfigs(var, args)
                bins = int(bins)
                min_val = int(min_val)
                max_val = int(max_val)

                fig, ax = self.createSubplots([var])

                self.plotHistogram(hdf5_file_path, var, ax, bins, min_val, max_val, color, alpha=0.3)

                ax.legend(fontsize=6)
                ax.set_title(var)

                plt.tight_layout()
                self.saveFigure(fig, var)

    def subPlot(self, args):
        logger.info("Plotting subplot variables: %s", self.vars)
        # Get list of HDF5 files in the output directory
        hdf5_files = [f for f in os.listdir(self.outdir) if f.endswith('.hdf5')]
        logger.info("Found HDF5 files: %s", hdf5_files)

        # Identify pairs of files
        pairs = self.identifyPairs(hdf5_files)
        logger.debug("Pairs: %s", pairs)

        for var in self.vars:
            # Create subplots for each var
            fig, axes = plt.subplots(len(pairs), 1, figsize=(10, 5 * len(pairs)))
            logger.debug("Plotting variable: %s", var)

            # Ensure axes is iterable even if there's only one subplot
            if len(pairs) == 1:
                axes = [axes]

            for i, (no_filter_file, filter_file) in enumerate(pairs):
                bins, min_val, max_val = self.config.readConfigs(var, args)
                bins = int(bins)
                min_val = int(min_val)
                max_val = int(max_val)

                ax = axes[i]  # Get the corresponding subplot axis

                self.plotHistogram(no_filter_file, var, ax, bins, min_val, max_val, color='blue', alpha=0.5)
                self.plotHistogram(filter_file, var, ax, bins, min_val, max_val, color='red', alpha=0.5)

                ax.legend(fontsize=6)
                ax.set_title(f'{var} - Pair {i+1}')

            plt.tight_layout()
            self.saveFigure(fig, var)




if __name__ == "__main__":
    stack = Stack()
