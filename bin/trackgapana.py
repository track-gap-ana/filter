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
import ConfigHelper

"""

Driver script for plotting and treeograming 

"""
logger = logging.getLogger(__name__)


class Make(object):
    def __init__(self):
        pass

    # general functions
    def emptyCheck(self, outdir, func):
        if os.listdir(outdir):
            if args.redo is True: 
                logging.info("Outdir is not empty. Redoing...")
                func()
            else:
                logging.error("Outdir is not empty. Use --redo to redo")
        else:
            func()

    # Corrected processOnline method
    def processOnline(self, args):
        online = Preprocess_condor.CondorFilter(args)
        outdir = online.check_socket()
        
        # Pass the function reference, not the result of its execution
        self.emptyCheck(args.outdir, online.process_online_files)

    # Corrected processOffline method
    def processOffline(self, args):
        fast = True if args.fast else False
        if args.dag is True:
            offline = Preprocess_condor.CondorFilter(args)
            outdir = offline.check_socket()
            outdir
            # Pass the function reference, not the result of its execution
            self.emptyCheck(outdir, offline.process_offline_files)
        else:
            offline = OfflinePreprocess.OfflineFilter(outdir=args.outdir, config_samples=args.config_samples, indir=args.sigs_path, fast=fast, dag=True)
            # Use a lambda if the function needs to be called with arguments
            self.emptyCheck(args.outdir, lambda: offline.run())

    # Corrected makeStackH5 method using lambda for passing arguments
    def makeStackH5(self, args):
        stack = VarCalculator.VarCalculator(args)
        self.emptyCheck(args.outdir, lambda: stack.localTrayLoop(args))

    # Corrected plotStack method using lambda for passing arguments
    def plotStack(self, args):
        plot = Plot.Stack(outdir=args.outdir, config_var=args.config_var, config_samples=args.config_samples)
        # self.emptyCheck(args.outdir, lambda: plot.onePlot(args=args))
        plot.onePlot(args)

    def plotStackSubplot(self, args):
        plot = Plot.Stack(outdir=args.outdir, config_var=args.config_var, config_samples=args.config_samples)
        # self.emptyCheck(args.outdir, lambda: plot.subPlot(args=args))
        plot.subPlot(args)

    # calling run functions
    def run(self,args):
        # set logging configs
        if args.debug is True:
            print('logger level is at debug')
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
            if args.subplot: self.plotStackSubplot(args)

        # make stack with new variables plotting
        if args.type == "yield":
            if args.plot: self.plotYield(args)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    default_config_var = "configs/variables.yaml"
    default_config_samples = "configs/samples.yaml"

    config = ConfigHelper.ConfigHelper(config_var=default_config_var , config_samples=default_config_samples)
    # Load the config_samples file
    default_sig_top = config.loadSig()
    default_bkg_top = config.loadBkg()
    default_gcd = config.loadGCD()

    # what do you want to do? 
    parser.add_argument('--type', '-t', choices=['online', 'offline', 'stack', 'yield'], required=True)
    
    parser.add_argument("--sigs_path", "-sp", default=default_sig_top, required=False, help="All signal simulation")
    parser.add_argument("--bkg_path", "-bp", default=default_bkg_top)
    parser.add_argument("--gcd_path", '-g', default=default_gcd, required=False)    
    parser.add_argument('--config-var', '-cv', default = default_config_var ,help="config yaml variable file")
    parser.add_argument('--config-samples', '-cs', default = default_config_samples ,help="config yaml samples file")    
    parser.add_argument('--outdir', "-o", default="outdir")

    # condor / DAGMan submission and relevant path finding only arguments
    parser.add_argument('--dag', '-D', action="store_true", help="Submit jobs to condor")
    parser.add_argument('--version', '-v', default="v1", help="Version of the output files")
    
    #turn on or off
    parser.add_argument('--fast', required=False, action="store_true", help="Run with flag for fast testing")
    parser.add_argument('--withbkg', "-B", action="store_true")
    parser.add_argument('--plot', '-P', action="store_true")
    parser.add_argument('--subplot', '-S', action="store_true")
    parser.add_argument('--var', '-V', action="store_true")
    parser.add_argument('--redo', '-R', action="store_true", help='Redo variable calculation and h5 file creation')
    parser.add_argument('--debug', '-d', action="store_true", help="Run with flag for debug logging")


    args = parser.parse_args()

    compile = Make()
    compile.run(args)