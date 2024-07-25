#!/usr/bin/env python
import icecube
from icecube import icetray, dataio, dataclasses, MuonGun, hdfwriter, simclasses
from icecube.icetray import I3Tray
import pandas as pd
import re
import yaml
import os
import logging

# set global logger
logger = logging.getLogger(__name__)

class ConfigHelper(object):
    def __init__(self, config_var=None, config_samples=None):
        self.config_var = config_var
        self.config_samples = config_samples
        pass
    
    def loadSamplesConfig(self):
        # Load the config_samples.yaml file
        with open(self.config_samples, 'r') as file:
            config_samples = yaml.safe_load(file)
        return config_samples
        
    def loadBkg(self):
        # Load the bkg key from the config_samples.yaml file
        config_samples = self.loadSamplesConfig()
        bkg = config_samples['bkg']
        return bkg
    
    def loadSig(self):
        # Load the sig key from the config_samples.yaml file
        config_samples = self.loadSamplesConfig()
        sig = list(config_samples['sig'].keys())[0]
        return sig

    
    def loadSigType(self):
        # Load the sig key from the config_samples.yaml file
        config_samples = self.loadSamplesConfig()
        top_dir = self.loadSig()
        sig_types = [config_samples['sig'][top_dir]]
        return sig_types

    def loadGCD(self):
        # Load the gcd key from the config_samples.yaml file
        config_samples = self.loadSamplesConfig()
        gcd = config_samples['gcd']
        return gcd

    def loadVersion(self):
        # Load the version key from the config_samples.yaml file
        config_samples = self.loadSamplesConfig()
        version = config_samples['version']
        return version

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
    
    def loadFilter(self):
        # Load the filter from the config_var.yaml file
        config_data = self.loadConfig()
        filter = config_data['filter']
        return filter
    
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

        for name, values in treeVars['vars'].items():
            bins, min_val, max_val = values

        return bins, min_val, max_val
    
    def makeDirs(self, directory):
        # Make the output directory if it does not exist
        if not os.path.exists(directory):
            logger.info(f"Making directory: {directory}")
            os.makedirs(directory)
        return directory
    
    def alter_name(self, sig_type, fast = False):
        if fast is True:
            print("fast mode")
            sig_type = "test"
        if "*" is sig_type:
            sig_type = "full"
        return sig_type.replace("*","")