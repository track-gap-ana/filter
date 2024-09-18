#!/usr/bin/env python3
"""
UnpackDST: A standalone script to unpack SuperDST PPfilt files from the South Pole and run offline filtering.

This script processes input i3 files using specified GCD file and applies various offline filters. It supports
command-line arguments to specify input/output files, logging levels, and other options.

Usage:
    python UnpackDST.py -i <input_file> -o <output_file> -g <gcd_file> [options]

Options:
    -i, --input        Input i3 file to process (required)
    -o, --output       Output i3 file (required)
    -g, --gcd          GCD file for input i3 file (required)
    --qify             Apply QConverter if input file contains only P frames
    -p, --prettyprint  Perform a big tray dump without processing
    -n, --num          Number of frames to process (default: -1 = all frames)
    --log-level        Set the logging level (ERROR, WARN, INFO, DEBUG, TRACE)
"""
import json
import os
import sys
import time
from argparse import ArgumentParser
from pathlib import Path

from icecube import dataclasses
from icecube import icetray
from icecube import phys_services
from icecube import dataio
from icecube.icetray import I3Tray
from icecube.icetray import logging as log
from icecube.offline_filterscripts.read_superdst_files import read_superdst_files


from icecube.icetray import I3Units

from icecube.STTools.seededRT.configuration_services import I3DOMLinkSeededRTConfigurationService
from icecube.phys_services.which_split import which_split

start_time = time.asctime()

# handling of command line arguments
parser = ArgumentParser(
    prog="readDST",
    description="Stand alone example to simulate pole unpacking")
parser.add_argument("-i", "--input", action="store", default=None,
                    dest="INPUT", help="Input i3 file to process", required=True)
parser.add_argument("-o", "--output", action="store", default=None,
                    dest="OUTPUT", help="Output i3 file", required=True)
parser.add_argument("-g", "--gcd", action="store", default=None,
                    dest="GCD", help="GCD file for input i3 file", required=True)
parser.add_argument("--qify", action="store_true", default=False, dest="QIFY",
                    help="Apply QConverter, use if input file is only P frames")
parser.add_argument("-p", "--prettyprint", action="store_true",
                    dest="PRETTY", help="Do nothing other than big tray dump")
parser.add_argument("-n","--num", default=-1, type=int, dest="NUM",
                        help="Number of frames to process (default: -1 = all frames)")
parser.add_argument("--log-level",
                    type=str, default="WARN", dest="LOG_LEVEL",
                    help="Sets the logging level (ERROR, [WARN], INFO, DEBUG, TRACE)")

args = parser.parse_args()

tray = I3Tray()

# Prep the logging hounds.
icetray.logging.console()   # Make python logging work
log_levels = {"error" : icetray.I3LogLevel.LOG_ERROR,
              "warn" : icetray.I3LogLevel.LOG_WARN,
              "info" : icetray.I3LogLevel.LOG_INFO,
              "debug" : icetray.I3LogLevel.LOG_DEBUG,
              "trace" : icetray.I3LogLevel.LOG_TRACE}

if args.LOG_LEVEL.lower() in log_levels.keys():
    icetray.set_log_level(log_levels[args.LOG_LEVEL.lower()])
else:
    icetray.logging.log_warn("log level option %s not recognized.")
    icetray.logging.log_warn("Options are ERROR, WARN, INFO, DEBUG, and TRACE.")
    icetray.logging.log_warn("Sticking with default of WARN.")
    icetray.set_log_level(icetray.I3LogLevel.LOG_WARN)

log.log_info(f"prog {parser.prog}")
name = parser.prog
log.log_info(f"name {name}")

log.log_info(f"Processing: {args.GCD} {args.INPUT}")

# Add the unpacking module to the tray
tray.Add(read_superdst_files, name + "_read_dst",
         input_files=[args.INPUT],
         input_gcd=args.GCD,
         qify_input=args.QIFY)

# Create a SeededRT configuration object with the standard RT settings.
seededRTConfig = I3DOMLinkSeededRTConfigurationService(
                     ic_ic_RTRadius              = 150.0*I3Units.m,
                     ic_ic_RTTime                = 1000.0*I3Units.ns,
                     treat_string_36_as_deepcore = False,
                     useDustlayerCorrection      = False,
                     allowSelfCoincidence        = True
                 )

# pulse clean
tray.AddModule('I3SeededRTCleaning_RecoPulseMask_Module', 'North_seededrt',
    InputHitSeriesMapName  = 'SplitInIcePulses',
    OutputHitSeriesMapName = 'SRTInIcePulses',
    STConfigService        = seededRTConfig,
    SeedProcedure          = 'HLCCoreHits',
    NHitsThreshold         = 2,
    MaxNIterations         = 3,
    Streams                = [icetray.I3Frame.Physics],
    If = which_split(split_name='InIceSplit')
)


# don't save GCD
tray.AddModule("I3Writer", "EventWriter", filename=args.OUTPUT, Streams=[icetray.I3Frame.DAQ,
                                                                        icetray.I3Frame.Physics,
                                                                        icetray.I3Frame.TrayInfo,
                                                                        icetray.I3Frame.Simulation,])

if args.PRETTY:
    log.log_info(str(tray))
    sys.exit(0)

if args.NUM >= 0:
    tray.Execute(args.NUM)
else:
    tray.Execute()

tray.PrintUsage(fraction=1.0)
for entry in tray.Usage():
    log.log_info(f"{entry.key()} : {entry.data().usertime}")

stop_time = time.asctime()
log.log_info(f"Started: {start_time}")
log.log_info(f"Ended: {stop_time}")
