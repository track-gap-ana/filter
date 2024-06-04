#!/usr/bin/env python
import icecube
from icecube import icetray, dataio, dataclasses, MuonGun, hdfwriter, simclasses
from icecube.icetray import I3Tray
import glob
import pandas as pd
import re
import logging
import os
import yaml

# set global logger
logger = logging.getLogger(__name__)

class PlotHelper(object):
    def __init__(self):
        pass

    def loadConfig(self):
        # Load the config_var.yaml file
        with open(self.config_var, 'r') as file:
            config_data = yaml.safe_load(file)
        return config_data
    
    def loadVars(self):
        # Load the keys from the config_var.yaml file
        config_data = self.loadConfig()
        vars = list(config_data['vars'].keys())
        return vars
    
    def loadColors(self):
        # Load the colors from the config_var.yaml file
        config_data = self.loadConfig()
        colors = list(config_data['attri']['colorblind'])
        return colors
    
    def parseLegend(self,fileName):
        mass_match = re.search(r".mass-(\d+)", fileName)
        mass_match = f"{float(mass_match.group(1))} GeV"
        
        eps = re.search(r"eps(-?\d+e-?\d+)", fileName)
        eps = f" {float(eps.group(1))} eps"

        nevents = re.search(r"\.nevents-(\d+)", fileName)
        nevents = f" {float(nevents.group(1))} events"

        ene = re.search(r'\d+e\d+_\d+e\d+', fileName)
        ene = f" {ene.group(0)} ene"

        gap = re.search(r"\_gap_(\d+)", fileName)
        if gap is not None: 
            gap = f" {float(gap.group(1))} m"
        else: 
            gap = " 50 m"

        legend = mass_match+eps+nevents+ene+gap
        return legend
    
    def readConfigs(self,var,args):

        with open(args.config_var, 'r') as f:
            treeVars = yaml.full_load(f)
        for var_name, values in treeVars['vars'][var].items():
            bins, min_val, max_val = values
            var_name = var_name
            print(f"Variable: {var_name}, Bins: {bins}, Min: {min_val}, Max: {max_val}")


        return var_name, bins, min_val, max_val