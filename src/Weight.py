#!/usr/bin/env python3

# SPDX-FileCopyrightText: © 2022 the SimWeights contributors
#
# SPDX-License-Identifier: BSD-2-Clause

from pathlib import Path

from I3Tray import I3Tray
from icecube import hdfwriter, simclasses
import simweights
import pandas as pd


class CorsikaWeight(object):
    def __init__(self):
        pass


    def makeWeights(self, hdf5):
 
    
        # load the hdf5 file that we just created using pandas
        file = pd.HDFStore(hdf5, "r")

        # instantiate the weighter object by passing the pandas file to it
        weighter = simweights.CorsikaWeighter(file)

        # create an object to represent our cosmic-ray primary flux model
        flux = simweights.GaisserH4a()

        # get the weights by passing the flux to the weighter
        weights = weighter.get_weights(flux)
        return weights

    

if __name__ == "__main__":
    bkg_weight = CorsikaWeight()
    bkg_weight.makehdf5()
