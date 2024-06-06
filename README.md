# microNN_filter

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
110.0_GeV_-1e-05_eps_50000.0_events_1e3_2e5_ene_100.0_m.csv  130.0_GeV_-5e-06_eps_10000.0_events_1e2_1e3_ene_50_m.csv  CORSIKA.csv
115.0_GeV_-5e-06_eps_250000.0_events_1e2_2e5_ene_50.0_m.csv  130.0_GeV_-5e-06_eps_10000.0_events_1e3_1e6_ene_50_m.csv  plots
115.0_GeV_-5e-06_eps_2500.0_events_1e2_1e4_ene_50.0_m.csv    CORSIKA_100nevents.hdf5
```

## 2. Histogram & Plotting: 

### Stacks

Plotting stacks for signal and backgorund (with background weights) can be done by using the `--plot` flag. An example run line is: 
`python src/trackgapana.py --plot --type stack` 


---
To do: 
- [] some version issue with HDF5... causing plotting to abort
