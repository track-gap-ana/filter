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

## 2. Histogram & Plotting: 

### Stacks

Plotting stacks for signal and backgorund (with background weights) can be done by using the `--plot` flag. An example run line is: 
`python src/trackgapana.py --plot --type stack` 


---
To do: 
- [] some version issue with HDF5... causing plotting to abort
