#!/usr/bin/env python
from icecube import icetray, dataio, dataclasses
from icecube.icetray import I3Tray
import argparse
import logging
import VarCalculator
import os


"""

Driver script for plotting and treeograming 

"""
logger = logging.getLogger(__name__)

class Make(object):
    def __init__(self):
        pass

    def makeStackH5(self, args):
        # Ensuring that the user wants to replace vars and checks that the outdir does not contain vars
        if args.redo is False and os.listdir(args.outdir):
            logging.error("Outdir is not empty. Aborting...")
        else:
            stack = VarCalculator.VarCalculator()
            stack.loopTray(args)    

        
    def plotStack(self, args):
        import Plot
        plot = Plot.Stack(filepath=args.outdir, config_var=args.config_var)
        plot.processHist(args=args)


    def run(self,args):
        # set logging configs
        if args.verbose is True: logging.basicConfig(level=logging.DEBUG)
        else: logging.basicConfig(level=logging.INFO)

        # make h5 files
        if args.var: self.makeStackH5(args)
        
        # make stack histogram and plot
        if args.type == "stack":
            if args.plot: self.plotStack(args)

        # make yields histogram and plot
        if args.type == "yield":
            if args.plot: self.plotYield(args)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # what do you want to do? 
    parser.add_argument('--type', '-t', choices=['stack', 'yield'], required=True)
    
    parser.add_argument("--sigs_path", "-sp", default="/data/user/axelpo/LLP-data/", required=False, help="All signal simulation")
    parser.add_argument("--bkg_path", "-bp", default="/data/sim/IceCube/2020/generated/CORSIKA-in-ice/20904/0198000-0198999/detector/")
    parser.add_argument("--gcd_path", '-g', default="/data/user/axelpo/LLP-at-IceCube/dark-leptonic-scalar-simulation/resources/GeoCalibDetectorStatus_2021.Run135903.T00S1.Pass2_V1b_Snow211115.i3.gz", required=False)    
    parser.add_argument('--config-var', '-cv', default = "configs/variables.yaml" ,help="config yaml variable file")
    parser.add_argument('--outdir', "-o", default="outdir")
    
    #turn on or off
    parser.add_argument('--fast', action="store_true", help="Run with flag for fast testing")
    parser.add_argument('--withbkg', "-B", action="store_true")
    parser.add_argument('--plot', '-P', action="store_true")
    parser.add_argument('--var', '-V', action="store_true")
    parser.add_argument('--redo', '-R', action="store_true", help='Redo varograming')
    parser.add_argument('--verbose', '-v', action="store_true", help="Run with flag for debug logging")


    args = parser.parse_args()

    compile = Make()
    compile.run(args)