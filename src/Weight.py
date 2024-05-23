#!/usr/bin/env python3

# SPDX-FileCopyrightText: © 2022 the SimWeights contributors
#
# SPDX-License-Identifier: BSD-2-Clause

from pathlib import Path

from I3Tray import I3Tray
from icecube import hdfwriter, simclasses
import simweights
import pandas as pd


class Weight(object):
    def __init__(self):
        pass

    def readFiles(self, bkg):
        filenamelist = sorted(str(f) for f in Path(bkg).glob("*zst"))
        return filenamelist
            
    def makehdf5(self, args):
        if args.fast is not None: frames = int(100)
        else: frames = float("inf")

        tray = I3Tray()
        tray.Add("I3Reader", FileNameList=self.readFiles(args.bkg_path))
        tray.Add(
            hdfwriter.I3HDFWriter,
            SubEventStreams=["InIceSplit"],
            keys=["PolyplopiaPrimary", "I3PrimaryInjectorInfo", "I3CorsikaWeight"],
            output=f"{args.outdir}/CORSIKA.hdf5",
        )
        tray.Execute(frames)
    def makeWeights(self, weightfile):
        hdffile = pd.HDFStore(weightfile, 'r')
        weighter = simweights.CorsikaWeighter(hdffile)
        # select flux spectrum desired
        flux = simweights.GaisserH4a()
        weights = weighter.get_weights(flux)
        return weights

    

if __name__ == "__main__":
    bkg_weight = Weight()
    bkg_weight.makehdf5(args)
