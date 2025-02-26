# microNN_filter
The following lines and defaults in the code are for cobalt users. Samples need to be redirected if using other machines. 
## Table of Contents

1. [Existing Pass3 Filters](#existing-pass3-filters)
    - [0a. Online: Prime simulation with Base Processing](#0a-online-prime-simulation-with-base-processing)
    - [0b. Offline: Prime simulation with Base Processing](#0b-offline-prime-simulation-with-base-processing)
2. [Variable Calculator](#variable-calculator)
3. [Histogram & Plotting](#histogram--plotting)
    - [Stacks](#stacks)
4. [Misc information and functionalities](#misc-information-and-functionalities)
    - [DAGman functionalities](#dagman-functionalities)
    - [Removing corrupt condor output files](#removing-corrupt-condor-output-files)
    - [Version controlling with git messages](#version-controlling-with-git-messages)

### Existing Pass3 Filters
Pull and checkout desired branch 

## 0a. Online: Prime simulation with Base Processing
Base process for filter studies done with online processing on the condor submission server `submit-1` using DAGMan submission formats.

### Usage:
#### Required:
`--type`, `--outdir`, `--config_samples`, `config_samples.yaml`, `--dag`
- sig subdirs
- gcd file path
- production version (zodiac nomenclature)

Non-standard module depedencies: 
- icetray version with whatever filters will be applied for testing later on

#### Options:
`--sig_path`
`--fast`
`--version`

#### Example usage:
Online: 

`python bin/trackgapana.py --type online --outdir /data/user/vparrish/llp_ana/online --version v1 --debug --dag --redo`

## 0b. Offline: Prime simulation with Base Processing
Base process for filter studies done with offline processing. This can be done locally or on the condor submission server `submit-1` using DAGMan submission formats.

### Usage:
Example useage found below.
#### Required:
`--type`, `--outdir`, `--sigs_path`
- sig subdirs
- gcd file path
- production version (zodiac nomenclature)
- `sigs_path` that is the path from the online preprocessing 

Non-standard module depedencies: 
- icetray version with whatever filters will be applied for testing later on

#### Options:
`--sig_path`
`--fast`
`--version`
`--dag`

##### Offline *without* DAGMan sub:

`python bin/trackgapana.py --type offline --outdir /data/user/vparrish/llp_ana/offline/ --sigs_path /data/user/vparrish/llp_ana/online/output/lateGemini/260624/full/ --fast --debug`

##### Offline *with* DAGMan sub: 

`python bin/trackgapana.py --type offline --outdir /data/user/vparrish/llp_ana/offline --sigs_path /data/user/vparrish/llp_ana/online/output/lateGemini/260624/full/ --fast --debug --dag`

##### Read SuperDST files ONLY (must be DAG submited):

`python bin/trackgapana.py --type offline --clean --outdir /data/user/vparrish/llp_ana/offline_clean --sigs_path /data/user/vparrish/llp_ana/online/output/lateGemini/260624/full/ --fast --debug --dag`

Notes: 
- the `sig_path` for the offline process must be the same as the `outdir` used in the online process
- the `outdir` should change to where ever you'd like to keep your offline process samples
- double check your `samples.yaml` config file before running. Please keep Zodaic version the same between online and offline processes.

## 1. Variable Calculator: 
##### Required:

`--type`
`--var`

##### Options:
`--dag` : use if you have produced the samples you want to use in the calculator were created with DAGMan (directory structure differences)
`--redo` : use if you have already created hdf5 files 
`--withbkg`
`--fast`
#### Background samples: 
Running to `--redo` the csv files already created with 100 events, explicit calling of the hist flags, and the type of histogram you're making is for later stack plots. Running `--withbkg` means you are doing bkg *only* calculations and stack booking. 

`python bin/trackgapana.py --redo --var --type stack --withbkg `

##### Signal samples: 

Same as bkg except without `--withbkg` flag
`python bin/trackgapana.py --redo --var --type stack`

When you have samples produced with DAGMan jobs: 
`python bin/trackgapana.py --var --type stack -sp /data/user/vparrish/llp_ana/offline/output/lateGemini/110724/test/ -o outdir/new_muon_filter/post_filter/apply --debug --dag --redo --fast` 

All event trees should now be in `.hdf5` files in your outdir, including your CORSIKA file (with calculated variables plus relevant variables for weighting during plotting), and signal files.

```
bash-4.2$ ls outdir/
(tga) bash-4.2$ ls outdir/June2024/
CORSIKA.hdf5                                                                                               DarkLeptonicScalar.mass-110.eps-3e-05.nevents-50000.0_ene_1000.0_10000.0_gap_75.0_240531.210876733.hdf5  plots
DarkLeptonicScalar.mass-110.eps-3e-05.nevents-150000.0_ene_2000.0_15000.0_gap_100.0_240602.210981234.hdf5  DarkLeptonicScalar.mass-115.eps-2e-5.nevents-50000_ene_1e2_1e4_gap_100_240510.208851130.hdf5
```

##### Data samples:

Supporting data samples with a signal score from a model in the frames. 

`python bin/trackgapana.py --var --type stack --data`

## 2. Histogram & Plotting: 

### Stacks
##### Required:

`--type`
`--outdir`
`--plot`

##### Options:
`--redo` : use if you have already created plots 

Plotting stacks for signal and backgorund (with background weights) can be done by using the `--plot` flag. An example run line is: 
`python bin/trackgapana.py --plot --type stack` 


## Misc information and functionalities

#### DAGman functionaliteis: 

*You need to first be signed into the `submit-1` submission cluster system through `pub.icecube`.*
Monitor jobs: 

`condor_q`

Resubmit failed subprocesses:
 - rerun the original python line from above

#### Removing corrupt condor output files

An independent script for removing corrupted files from failed or retired condor jobs.

##### Usage

`python bin/dagcheck.py --folder path/to/bad/jobs` 

In this instance, you will be compiling a list of files that failed the frame check. It is written to `bad_files.txt`. You have the option to run with the `--remove-bad` flag if you know the files you want to identify as bad you must immediately remove.

Otherwise, you may run separately:

`python bin/dagcheck.py --folder path/to/bad/jobs --remove-bad` 

This will first check to make sure that the `bad_files.txt` exists, and if it does, to just remove the files saved in that file. 

#### Version controlling with git messages

In filter sample productions, plot alterations, etc, you may commit the current repo. Please add `-m "your commit message"` to your run line. This will take a snapshot of the current repo + the run line + timestamp and commit to your branch. 