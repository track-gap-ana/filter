# microNN_filter
The following lines and defaults in the code are for cobalt users. Samples need to be redirected if using other machines. 

## 1. Variable Calculator: 

#### Background samples: 
Running to `--redo` the csv files already created with 100 events, explicit calling of the hist flags, and the type of histogram you're making is for later stack plots. Running `--withbkg` means you are doing bkg *only* histograming. 

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
