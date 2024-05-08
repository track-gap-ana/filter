#!/usr/bin/env python
import icecube
from icecube import icetray, dataio, dataclasses, MuonGun
from icecube.icetray import I3Tray
import glob
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import argparse
import pandas as pd
import re
import logging
import os
import yaml
import Plot
import Hist

"""

Driver script for plotting and histograming 

"""

class Make(object):
    def __init__(self):
        pass
    
    def makeStackHist(self, args):
        # Ensuring that the user wants to replace histograms and checks that the outdir does not contain histograms
        if args.redo is True and ("*.csv" in list(glob.glob(args.outdir))):
            stack = Hist.Stack()
            stack.makeHist(args)
        else:
            logging.error("Outdir is not empty")
            pass
    
    # def makeYieldHist(self, args):
    #     if args.redo is True and ("yield.csv" in list(glob.glob(args.outdir))):
    #         # Redo yields hist 
    #     else:
    #         logging.error("Outdir is not empty")
    #         pass
        
    def plotStack(self):
        plot = Plot.Stack(histpath=args.outdir, config_var=args.config_var)
        plot.processHist()


    def run(self,args):
        # if plot flag is used, plot
        if args.type is "stack":
            if args.hist: self.makeStackHist(args)
            if args.plot: self.plotStack()
        if args.type is "yield": 
            if args.hist: self.makeYieldHist(args)
            if args.plot: self.plotYield()
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--sigs_path", "-sp", default="/data/user/axelpo/LLP-data/", required=False, help="All signal simulation")
    parser.add_argument("--gcd_path", '-g', default="/data/user/axelpo/LLP-at-IceCube/dark-leptonic-scalar-simulation/resources/GeoCalibDetectorStatus_2021.Run135903.T00S1.Pass2_V1b_Snow211115.i3.gz", required=False)    
    parser.add_argument('--config-var', '-cv', default = "configs/variables.yaml" ,help="config yaml variable file")
    parser.add_argument("--weight", "-w", type=float, required=False)
    parser.add_argument('--outdir', "-o", default="outdir")
    
    #turn on or off
    parser.add_argument('--withbkg', "-b", action="store_true")
    parser.add_argument('--plot', '-p', action="store_true")
    parser.add_argument('--hist', action="store_true")
    parser.add_argument('--redo', '-r', action="store_true")
    parser.add_argument('--fast', '-f', action="store_true", help="Run with flag if you want to a small multiple signal sample set test")

    # histo and plotting types
    parser.add_argument('--type', 't', options=['stack', 'yield'], required=True)

    args = parser.parse_args()

    compile = Make()
    compile.run(args)