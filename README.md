# microNN_filter
The following lines and defaults in the code are for cobalt users. Samples need to be redirected if using other machines. 
### Existing Pass3 Filters
Pull and checkout desired branch 

## 0. Prime simulation with Base Processing
Base process for filter studies done with online and offline filter processing on the condor submission server `submit-1` using DAGMan submission formats.

### Usage:
#### Required:
`--type`, `--outdir`, `--config_samples`, 
config_samples.yaml
- sig subdirs
- gcd file path
- production version (zodiac nomenclature)
Depedencies: 
- icetray version with whatever filters will be applied for testing later on

#### Options:
`--sig_path`
`--fast`
`--version`

#### Example usage:
Online: 
`python src/trackgapana.py --type online --outdir /data/user/vparrish/llp_ana/online --fast --version v1`
##### Not completely integrated functionality yet -- do not run yet
Offline:
`python src/trackgapana.py --type online --sig_path /data/user/vparrish/llp_ana/online --fast --version v1`
Notes: 
- the `sig_path` for the offline process must be the same as the `outdir` used in the online process
- the `outdir` should change to whereever you'd like to keep your offline process samples
#### DAGman functionaliteis: 
Monitor jobs: 
`condor_q`
Resubmit failed subprocesses:
 - rerun the original python line from above

## 1. Variable Calculator: 

#### Background samples: 
Running to `--redo` the csv files already created with 100 events, explicit calling of the hist flags, and the type of histogram you're making is for later stack plots. Running `--withbkg` means you are doing bkg *only* calculations and stack booking. 

`python src/trackgapana.py --redo --var --type stack --withbkg `

##### Signal samples: 

Same as bkg except without `--withbkg` flag
`python src/trackgapana.py --redo --var --type stack`

All event trees should now be in `.hdf5` files in your outdir, including your CORSIKA file (with calculated variables plus relevant variables for weighting during plotting), and signal files.

```
bash-4.2$ ls outdir/
(tga) bash-4.2$ ls outdir/June2024/
CORSIKA.hdf5                                                                                               DarkLeptonicScalar.mass-110.eps-3e-05.nevents-50000.0_ene_1000.0_10000.0_gap_75.0_240531.210876733.hdf5  plots
DarkLeptonicScalar.mass-110.eps-3e-05.nevents-150000.0_ene_2000.0_15000.0_gap_100.0_240602.210981234.hdf5  DarkLeptonicScalar.mass-115.eps-2e-5.nevents-50000_ene_1e2_1e4_gap_100_240510.208851130.hdf5
```

## 2. Histogram & Plotting: 

### Stacks

Plotting stacks for signal and backgorund (with background weights) can be done by using the `--plot` flag. An example run line is: 
`python src/trackgapana.py --plot --type stack` 
