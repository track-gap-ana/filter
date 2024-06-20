#!/usr/bin/env python
import os
import argparse
import logging
import yaml

import VarCalculator
import Plot
import OnlinePreprocess_condor


"""

Driver script for plotting and treeograming 

"""
logger = logging.getLogger(__name__)


class Make(object):
    def __init__(self):
        pass
    
    # general functions
    def redo(self, outdir, func):
        if os.listdir(outdir):
            logging.error("Outdir is not empty. Aborting...")
        else:
            func
            return True
        
    def assertConfig(self, args, warning):

        # Load the config samples file
        with open(args.config_samples, 'r') as file:
            config_samples = yaml.safe_load(file)

        # Check if the sig key in the config samples file is the same as the provided path
        if list(config_samples['sig'].keys())[0] != args.sigs_path:
            logging.warning(f"The sig top directory in config_samples.yaml does not match the provided path. {warning}.")
    
    # specific functions
    def processOnline(self,args):
        # check samples path consistency
        self.assertConfig(args, "Using config_samples.yaml provided path.")

        # execute online processing
        online = OnlinePreprocess_condor.Online(args)
        online.process_files()

    def makeStackH5(self, args):
        stack = VarCalculator.VarCalculator()
        
        if args.redo is True: self.redo(args.outdir, stack.loopTray(args))
        else : stack.loopTray(args)

    def plotStack(self, args):
        plot = Plot.Stack(filepath=args.outdir, config_var=args.config_var)
        plot.processHist(args=args)

    # calling run functions
    def run(self,args):
        # set logging configs
        if args.debug is True:
            logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        else:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # Define custom log colors
        logging.addLevelName(logging.DEBUG, "\033[1;34m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))
        logging.addLevelName(logging.INFO, "\033[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO))
        logging.addLevelName(logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
        logging.addLevelName(logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))

        # make h5 files
        if args.var: self.makeStackH5(args)
        
        # make online files
        if args.type == "online":
            self.processOnline(args)

        # make stacks with new variables
        if args.type == "stack":
            if args.plot: self.plotStack(args)

        # make stack with new variables plotting
        if args.type == "yield":
            if args.plot: self.plotYield(args)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # what do you want to do? 
    parser.add_argument('--type', '-t', choices=['online', 'offline', 'stack', 'yield'], required=True)
    
    parser.add_argument("--sigs_path", "-sp", default="/data/user/axelpo/LLP-data/", required=False, help="All signal simulation")
    parser.add_argument("--bkg_path", "-bp", default="/data/sim/IceCube/2020/generated/CORSIKA-in-ice/20904/0198000-0198999/detector/")
    parser.add_argument("--gcd_path", '-g', default="/data/user/axelpo/LLP-at-IceCube/dark-leptonic-scalar-simulation/resources/GeoCalibDetectorStatus_2021.Run135903.T00S1.Pass2_V1b_Snow211115.i3.gz", required=False)    
    parser.add_argument('--config-var', '-cv', default = "configs/variables.yaml" ,help="config yaml variable file")
    parser.add_argument('--config-samples', '-cs', default = "configs/samples.yaml" ,help="config yaml samples file")    
    parser.add_argument('--outdir', "-o", default="outdir")
    
    #turn on or off
    parser.add_argument('--fast', required=False, action="store_true", help="Run with flag for fast testing")
    parser.add_argument('--withbkg', "-B", action="store_true")
    parser.add_argument('--plot', '-P', action="store_true")
    parser.add_argument('--var', '-V', action="store_true")
    parser.add_argument('--redo', '-R', action="store_true", help='Redo varograming')
    parser.add_argument('--debug', '-d', action="store_true", help="Run with flag for debug logging")


    args = parser.parse_args()

    compile = Make()
    compile.run(args)