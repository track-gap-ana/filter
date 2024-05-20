# microNN_filter
## Histograming: 

### Example line:

#### Background histograms: 
Running to redo the csv files already created with 1000 events, explicit calling of the hist flags, and the type of histogram you're making is for later stack plots. Running `--withbkg` means you are doing bkg only histograming. 

`python src/trackgapana.py --redo --nevents 1000 --hist --type stack --withbkg `

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

## Plotting: 

Yeah... okay something else needs to be done about weighting corsika with the variables already selected and histogramed :/ 