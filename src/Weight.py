#!/usr/bin/env python3

# SPDX-FileCopyrightText: © 2022 the SimWeights contributors
#
# SPDX-License-Identifier: BSD-2-Clause

import pandas as pd
import pylab as plt
from pathlib import Path
import glob
from I3Tray import I3Tray
from icecube import hdfwriter, simclasses

import simweights

class Weight(object):
    def __init__(self):
        pass

    def bkgWeight(self, args, h5file):

        # load the hdf5 file that we just created using pandas
        hdfstore = pd.HDFStore(h5file, "r")

        # initiate nfiles used in bkg hist production
        if args.nfiles is not None: nfiles =  args.nfiles
        else : nfiles = len(glob.glob(args.bkg_path))

        weighter = simweights.CorsikaWeighter(hdfstore, nfiles)

        # create an object to represent our cosmic-ray primary flux model
        flux = simweights.GaisserH4a()

        # get the weights by passing the flux to the weighter
        bkg_weights = weighter.get_weights(flux)

        return bkg_weights

if __name__ == "__main__":
    bkg_weight = Weight()
    bkg_weight.bkgWeight()