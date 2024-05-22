# microNN_filter

## 1. CORSIKA Weights: 
First, you need to produce your CORSIKA weights. That is done in the `Weights.py` class. 


All you need to provide to this is the weight flag, but you can also pass a `nevents` flag if you are doing a fast test. Make sure if you use `--fast` you use it for the histograming portion too:

`python src/trackgapana.py --redo --fast --weight`

These weights should be saved to the same directory as your simulation files. 

todo: 
[] @axel itegrate this functionality into the simulation framework instead of the histograming one...? 
[] Need to alter VarCalculator to be able to calculate the variables we are using in hdf5 and not just i3 files... this seems stupid. Maybe it's worth getting in touch with the simweights people... 

## 2. Histograming: 

#### Background histograms: 
Running to redo the csv files already created with 1000 events, explicit calling of the hist flags, and the type of histogram you're making is for later stack plots. Running `--withbkg` means you are doing bkg only histograming. 

`python src/trackgapana.py --redo --fast --hist --type stack --withbkg `

##### Signal histograms: 
Same as bkg except without `--withbkg` flag
`python src/trackgapana.py --redo --hist --type stack`

Creates dir of histograms in desired outdir, also customizable. `CORSIKA.hdf5` is only used for plot weighting later on. 

```
bash-4.2$ ls outdir/
110.0_GeV_-1e-05_eps_50000.0_events_1e3_2e5_ene_100.0_m.csv  130.0_GeV_-5e-06_eps_10000.0_events_1e2_1e3_ene_50_m.csv  forbkgweighting.hdf5
115.0_GeV_-5e-06_eps_250000.0_events_1e2_2e5_ene_50.0_m.csv  130.0_GeV_-5e-06_eps_10000.0_events_1e3_1e6_ene_50_m.csv  plots
115.0_GeV_-5e-06_eps_2500.0_events_1e2_1e4_ene_50.0_m.csv    CORSIKA.csv
bash-4.2$ 
```

## 3. Plotting: 

Yeah... okay something else needs to be done about weighting corsika with the variables already selected and histogramed :/ 