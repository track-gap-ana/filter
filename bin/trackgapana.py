#!/usr/bin/env python
import os
import argparse
import logging
import yaml

import VarCalculator
import Plot
import OfflinePreprocess
import Preprocess_condor
import Logging

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
        
    def checkConfig(self, args, warning):

        # Load the config samples file
        with open(args.config_samples, 'r') as file:
            config_samples = yaml.safe_load(file)

        # Check if the sig key in the config samples file is the same as the provided path
        if list(config_samples['sig'].keys())[0] != args.sigs_path:
            logging.warning(f"The sig top directory in config_samples.yaml does not match the provided path. {warning}.")
    
    # specific functions
    def processOnline(self,args):
        # check samples path consistency
        self.checkConfig(args, "Using config_samples.yaml provided path.")

        # execute online processing
        online = Preprocess_condor.CondorFilter(args)
        online.process_online_files()
    
    def processOffline(self,args):
        # execute offline processing
        # sigs_path should be the outdir of the online processing
        fast = True if args.fast else False
        if args.dag is True:
            offline = Preprocess_condor.CondorFilter(args)
            offline.process_offline_files()
        else:
            offline = OfflinePreprocess.OfflineFilter(outdir=args.outdir, config_samples=args.config_samples, indir=args.sigs_path, fast=fast, dag=True)
            offline.run()

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

        # Set special logging colors and rules
        Logging.specialRules()

        # make h5 files
        if args.var: self.makeStackH5(args)
        
        # make online files
        if args.type == "online":
            self.processOnline(args)
        
        # make offline files from online files
        if args.type == "offline":
            self.processOffline(args)

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

    # condor / DAGMan submission only arguments
    parser.add_argument('--dag', '-D', action="store_true", help="Submit jobs to condor")
    parser.add_argument('--version', '-v', default="v1", help="Version of the output files")
    
    #turn on or off
    parser.add_argument('--fast', required=False, action="store_true", help="Run with flag for fast testing")
    parser.add_argument('--withbkg', "-B", action="store_true")
    parser.add_argument('--plot', '-P', action="store_true")
    parser.add_argument('--var', '-V', action="store_true")
    parser.add_argument('--redo', '-R', action="store_true", help='Redo variable calculation and h5 file creation')
    parser.add_argument('--debug', '-d', action="store_true", help="Run with flag for debug logging")


    args = parser.parse_args()

    compile = Make()
    compile.run(args)