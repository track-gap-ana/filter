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

class ConfigureSamples():
    def __init__(self, outdir, config_var, config_samples):
        self.config=ConfigHelper.ConfigHelper(config_var=config_var, config_samples=config_samples)
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
    
    # This should be depreciated
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

class HistogramStack():
    def __init__(self, config_var, config_samples):
        self.config=ConfigHelper.ConfigHelper(config_var=config_var, config_samples=config_samples)
        self.model, self.wps = self.config.loadModel()

    def totalHistogram(self, file_path, var, ax, bins, min_val, max_val, color, alpha):
        """
        Defines a histogram from data stored in an HDF5 file to ber used for plotting
        """

        with h5py.File(file_path, 'r') as hdf5_file:
            data = np.asarray(hdf5_file[var]['value'][:], dtype=float)
            frame_count = len(hdf5_file[var]['value'])
            # logger.debug(f"Reading file: {file_path}\n Histogram related: {data}")
            if "CORSIKA" in file_path:
                corsikaweight = CorsikaWeight()
                weights = corsikaweight.makeWeights(file_path)
                ax.hist(data, histtype='step', bins=bins, range=(min_val, max_val), color=color, alpha=alpha, label="CORSIKA", weights=weights)
            else:
                title,legend = ConfigureSamples.getLabels(file_path)
                legend += f" Saved events: {frame_count}"
                ax.hist(data, histtype='step', bins=bins, range=(min_val, max_val), color=color, alpha=alpha, label=legend)
    
    def cutHistogram(self, file_path, var, wp, ax, bins, min_val, max_val, color, alpha):
        """
        Defines a histogram from selected data of passed working points stored in an HDF5 file to ber used for plotting
        """
        with h5py.File(file_path, 'r') as hdf5_file:
            data = np.asarray(hdf5_file[var]['value'][:], dtype=float)
            model_selection = np.asarray(hdf5_file[self.model]['value'][:], dtype=float)
            selected_data = data[model_selection > self.wp]
            frame_count = len(selected_data)
            legend += ConfigHelper.getLabels(file_path)
            ax.hist(selected_data, histtype='step', bins=bins, range=(min_val, max_val), color=color, alpha=alpha, label=f"{legend} WP: {wp} Events: {frame_count}")

class PlotStack():
    def __init__(self, outdir, config_var, config_samples):
        # Load the local supporting classes
        self.configure_samples = ConfigureSamples(outdir, config_var, config_samples)
        self.histogram_stack = HistogramStack(config_var, config_samples)
        self.save_stack = SaveStack()
        
        # Load the configuration settings
        self.config=ConfigHelper.ConfigHelper(config_var=config_var, config_samples=config_samples)
        self.vars = self.config.loadVars()
        self.colors = self.config.loadColors()
        self.outdir = self.config.makeDirs(outdir)
        

    def onePlot(self, args):
        """
        Generates and displays a plot for each variable in self.vars.

        Args:
            args: Additional arguments that may be required for reading configurations.

        The method performs the following steps:
         Iterates over each variable in self.vars.
         Creates a new figure for the plot.
         Reads HDF5 file paths and corresponding colors.
         Reads configuration settings (bins, min_val, max_val) for the variable.
         Converts bins, min_val, and max_val to integers.
         Calls self.totalHistogram to generate the histogram for the variable.
         Adds a legend to the plot.
         Displays the plot.
         Saves the figure using SaveStack.saveFigure.

        Note:
            The alpha value for the histogram is set to 0.3 if "CORSIKA" is in the HDF5 file path, otherwise it is set to 0.5.
        """
        for var in self.vars:
            logger.info("Plotting variable: %s", var)
            plt.figure()
            for hdf5_file_path, color in zip(self.configure_samples.hdf5Reader(self.outdir), self.colors):
                logger.debug(f"Variable: {var}")
                bins, min_val, max_val = self.config.readConfigs(var, args)
                bins = int(bins)
                min_val = int(min_val)
                max_val = int(max_val)

                self.histogram_stack.totalHistogram(hdf5_file_path, var, plt.gca(), bins, min_val, max_val, color, alpha=0.3 if "CORSIKA" in hdf5_file_path else 0.5)

            plt.legend(fontsize=6)
            plt.show()
            self.save_stack.saveFigure(plt.gcf(), var)

    def selectionsPlot(self, args):
        """
        Generates and displays plots for each variable in self.vars with and without a wp selection.

        Args:
            args: Additional arguments that may be required for reading configurations.
        """
        
        for var in self.vars:
            logger.info("Plotting variable with and without WP: %s", var)
            plt.figure()
            for hdf5_file_path, color in zip(self.configure_samples.hdf5Reader(self.outdir), self.colors):
                logger.debug(f"Variable: {var}")
                bins, min_val, max_val = self.config.readConfigs(var, args)
                bins = int(bins)
                min_val = int(min_val)
                max_val = int(max_val)

                # Plot total histogram
                self.histogram_stack.totalHistogram(hdf5_file_path, var, plt.gca(), bins, min_val, max_val, color, alpha=0.3 if "CORSIKA" in hdf5_file_path else 0.5)

                # Plot cut histogram for each WP
                for wp in self.wps:
                    self.histogram_stack.cutHistogram(hdf5_file_path, var, wp, plt.gca(), bins, min_val, max_val, color, alpha=0.3 if "CORSIKA" in hdf5_file_path else 0.5)
 
            plt.legend(fontsize=6)
            plt.show()
            self.save_stack.saveFigure(plt.gcf(), var, self.outdir)

    """
    This should be depreciated -- instead of creating two different hdf5 files with different selections, we are going to make the selections in the Histogram class in this file instead
    """
    def subPlot(self, args):
        
        logger.info("Plotting subplot variables: %s", self.vars)
        # Get list of HDF5 files in the output directory

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

                self.totalHistogram(no_filter_file, var, ax, bins, min_val, max_val, color='blue', alpha=0.5)
                self.totalHistogram(filter_file, var, ax, bins, min_val, max_val, color='red', alpha=0.5)
                
                title, _ = self.getLabels(filter_file, titleOnly=True)

                ax.set_yscale('log')
                ax.legend(fontsize=6)
                ax.set_xlabel(var)
                ax.set_ylabel("NEvents")
                ax.set_title(f'{title} - Pair {i+1}')
                
            plt.tight_layout()

            SaveStack.saveFigure(fig, var)

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

                self.totalHistogram(no_filter_file, var, plt.gca(), bins, min_val, max_val, color='blue', alpha=0.5)
                self.totalHistogram(filter_file, var, plt.gca(), bins, min_val, max_val, color='red', alpha=0.5)
                title,_ = self.getLabels(no_filter_file, titleOnly=True)
                plt.yscale('log')
                plt.legend(fontsize=6)
                plt.xlabel(var)
                plt.title(title)
                plt.ylabel("NEvents")
                plt.show()
                fig_path = var+"_"+filter_file.split('/')[-1].replace('.hdf5','')
                figure_paths.append(os.path.abspath(fig_path))
                SaveStack.saveFigure(plt.gcf(), fig_path)


        # self.generate_slide_deck(figure_paths)
    
class SaveStack():
    def __init__(self):
        self.config=ConfigHelper.ConfigHelper()
        pass

    def saveFigure(self, fig, var, outdir):
        self.plotspath = self.config.makeDirs(os.path.join(outdir, "plots"))
        figpath = os.path.join(self.plotspath, f"{var}.png")
        plt.savefig(figpath)
        logger.debug(f"Saved figure: {figpath}")
        plt.close(fig)

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
    stack = PlotStack()
