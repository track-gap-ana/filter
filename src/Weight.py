#!/usr/bin/env python3

# SPDX-FileCopyrightText: © 2022 the SimWeights contributors
#
# SPDX-License-Identifier: BSD-2-Clause

from pathlib import Path

from I3Tray import I3Tray
from icecube import hdfwriter, simclasses
import yaml
import glob
import logging


class Weight(object):
    def __init__(self):
        pass

    def readFiles(self, bkg):
        filenamelist = sorted(str(f) for f in Path(bkg).glob("*zst"))
        return filenamelist
    
    def readKeys(self, config_var):
        with open(config_var, 'r') as f:
            config = yaml.full_load(f)
            # loading baseline variables that are required in calculator
            l_Vars = config['vars'][0]['var']
            logging.info(f"Variables to be read from the config file: {l_Vars}")
            return l_Vars
            
    def makehdf5(self, args):
        if args.fast is not None: frames = int(100)
        else: frames = float("inf")

        tray = I3Tray()
        tray.Add("I3Reader", FileNameList=self.readFiles(args.bkg_path))
        tray.Add(
            hdfwriter.I3HDFWriter,
            SubEventStreams=["InIceSplit"],
            keys=self.readKeys(args.config_var),
            output=f"{args.outdir}/CORSIKA.hdf5",
        )
        tray.Execute(frames)
    

if __name__ == "__main__":
    bkg_weight = Weight()
    bkg_weight.bkgWeight()