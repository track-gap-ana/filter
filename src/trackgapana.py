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

    def makeHist(self, args):
        if args.redo is True:
            stack = Hist.Hist()
            stack.makeHist(args)
        else:
            logging.info("Outdir is not empty")
            pass
        
    def plot(self):
        plot = Plot.Stack(histpath=args.outdir, config_var=args.config_var)
        plot.processHist()

    def run(self,args):
        # if plot flag is used, plot
        if args.hist: self.makeHist(args)
        if args.plot: self.plot()
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--sigs_path", "-sp", default=None, required=False, help="All signal simulation")
    parser.add_argument("--test_sig", "-ts", default="/data/user/axelpo/LLP-data/DarkLeptonicScalar.mass-115.eps-5e-6.nevents-250000_ene_1e2_2e5_gap_50_240202.203241628", required=False, help="A single filelist from sig simulation sample")
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
    args = parser.parse_args()

    compile = Make()
    compile.run(args)