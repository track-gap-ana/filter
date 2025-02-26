#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np
import os
import logging
from Weight import CorsikaWeight
import h5py
import subprocess
import re
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
        
    def getLabels(self, file_path, titleOnly=False):
        legend = ' '.join((file_path.split('/')[-1]).replace('.', ' ').replace('_', ' ').replace('-', ' ').split()[:-4])
        title = ""  # Initialize title to an empty string
        if "noSelection" in file_path and titleOnly == False:
            legend += " No Selection"
        if "filter" in file_path and titleOnly == True:
            title = "Pre and post new muon filter"
        return title, legend
    
    def identifyH5Pairs(self):
        hdf5_files = [f for f in os.listdir(self.outdir) if f.endswith('.hdf5')]
        logger.info("Found HDF5 files: %s", hdf5_files)
        pairs = []
        for file in hdf5_files:
            if 'noSelection' in file:
                base_name = file.replace('_noSelection', '')
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
            frame_count = len(hdf5_file[var]['value'])
            # logger.debug(f"Reading file: {file_path}\n Histogram related: {data}")
            if "CORSIKA" in file_path:
                corsikaweight = CorsikaWeight()
                weights = corsikaweight.makeWeights(file_path)
                ax.hist(data, histtype='step', bins=bins, range=(min_val, max_val), color=color, alpha=alpha, label="CORSIKA", weights=weights)
            else:
                title,legend = self.getLabels(file_path)
                legend += f" Saved events: {frame_count}"
                ax.hist(data, histtype='step', bins=bins, range=(min_val, max_val), color=color, alpha=alpha, label=legend)

    def countFrames(self, var):
        pairs = self.identifyH5Pairs()
        for file_pair in pairs:
            for file in file_pair:
                with h5py.File(file, 'r') as hdf5_file:
                    frame_count = len(hdf5_file[var]['value'])
                    logger.debug(f"Processing file: {file}, Frame count: {frame_count}")
    
    def saveFigure(self, fig, var):
        self.plotspath = self.config.makeDirs(os.path.join(self.outdir, "plots"))
        figpath = os.path.join(self.plotspath, f"{var}.pdf")
        plt.savefig(figpath)
        logger.debug(f"Saved figure: {figpath}")
        plt.close(fig)

    def onePlot(self, args):
        for var in self.vars:
            logger.info("Plotting variable: %s", var)
            plt.figure()
            for hdf5_file_path, color in zip(self.hdf5Reader(self.outdir), self.colors):
                logger.debug(f"Variable: {var}")
                bins, min_val, max_val = self.config.readConfigs(var, args)
                bins = int(bins)
                min_val = int(min_val)
                max_val = int(max_val)

                self.plotHistogram(hdf5_file_path, var, plt.gca(), bins, min_val, max_val, color, alpha=0.3 if "CORSIKA" in hdf5_file_path else 0.5)

            plt.legend(fontsize=6)
            plt.show()
            self.saveFigure(plt.gcf(), var)


    def subPlot(self, args):
        logger.info("Plotting subplot variables: %s", self.vars)
        # Get list of HDF5 files in the output directory

        # Identify pairs of files
        pairs = self.identifyH5Pairs()
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
                
                title, _ = self.getLabels(filter_file, titleOnly=True)

                ax.set_yscale('log')
                ax.legend(fontsize=6)
                ax.set_xlabel(var)
                ax.set_ylabel("NEvents")
                ax.set_title(f'{title} - Pair {i+1}')
                
            plt.tight_layout()

            self.saveFigure(fig, var)

        self.plotPairs(args)

        logger.debug(self.countFrames(self.vars[0]))

    def plotPairs(self,args):

        #Identify pairs of files -- returns list of pairs
        pairs = self.identifyH5Pairs()
        figure_paths = []
        logger.debug("Pairs: %s", pairs)
        for var in self.vars:
            logger.info("Plotting variable: %s", var)
            plt.figure()
            for i, (no_filter_file, filter_file) in enumerate(pairs):
                logger.debug(f"Variable: {var}")
                bins, min_val, max_val = self.config.readConfigs(var, args)
                
                # Ensure bins, min_val, and max_val are of type float
                bins = int(bins)
                min_val = int(min_val)
                max_val = int(max_val)

                self.plotHistogram(no_filter_file, var, plt.gca(), bins, min_val, max_val, color='blue', alpha=0.5)
                self.plotHistogram(filter_file, var, plt.gca(), bins, min_val, max_val, color='red', alpha=0.5)
                title,_ = self.getLabels(no_filter_file, titleOnly=True)
                plt.yscale('log')
                plt.legend(fontsize=6)
                plt.xlabel(var)
                plt.title(title)
                plt.ylabel("NEvents")
                plt.show()
                fig_path = var+"_"+filter_file.split('/')[-1].replace('.hdf5','')
                figure_paths.append(os.path.abspath(fig_path))
                self.saveFigure(plt.gcf(), fig_path)

        # self.generate_slide_deck(figure_paths)
    
    def generate_slide_deck(self, figure_paths):
        # Generate the LaTeX slide deck
        slide_deck_path = os.path.join(self.plotspath, "slide_deck.tex")
        with open(slide_deck_path, 'w') as slide_deck:
            slide_deck.write("\\documentclass{beamer}\n")
            slide_deck.write("\\usepackage{graphicx}\n")
            slide_deck.write("\\begin{document}\n")

            for fig_path in figure_paths:
                fig_path = self.escape_latex_special_chars(fig_path)
                slide_deck.write(f"% Including figure: {fig_path}\n")
                slide_deck.write("\\begin{frame}\n")
                slide_deck.write(f"\\includegraphics[width=\\textwidth]{{{fig_path}}}\n")
                slide_deck.write("\\end{frame}\n")

            slide_deck.write("\\end{document}\n")

        # Compile the slide deck using pdflatex
        result = subprocess.run(["pdflatex", slide_deck_path], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"pdflatex compilation failed: {result.stderr}")
        else:
            logger.debug(f"Slide deck created: {slide_deck_path}")

if __name__ == "__main__":
    stack = Stack()
