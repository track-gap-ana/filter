""" Open two hdf5 files (online and offline) and plot survival rates filters using functions in plot_functions.py
"""

import os
import argparse

import tables
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from plot_functions import *


# Get params from parser
parser = argparse.ArgumentParser(description="Create plots online vs. offline")
parser.add_argument("--online", action="store",
    type=str, help=".hdf5 online")

parser.add_argument("--offline", action="store",
    type=str, help=".hdf5 offline")

parser.add_argument('--plot-folder', action="store",
    type=str, dest="plot-folder",
    help="folder to save plots")

parser.add_argument("--filtermask", action="store", default="OfflineFilterMask",
    type=str, help="name of filtermask in offline hdf5")

parser.add_argument('--cutoff',
                    type=float, default=0.0,
                    help='Min survival rate [0,1] to be plotted. Default is 0.0')

params = vars(parser.parse_args())  # dict()

# function to get df from hdf5
def df_from_hdf(hdffile,
                interesting_tables,
                uninteresting_cols_dict, # dict {table_name: [col1, col2, ...]}
                ):
    """ Create dataframe from hdf5 file from interesting tables and drop uninteresting columns in each table """
    dfs = []
    for key in interesting_tables:
        good_table = hdffile.root[key]
        df = pd.DataFrame.from_records(good_table.read())
        if key in uninteresting_cols_dict:
            df = df.drop(columns = uninteresting_cols_dict[key], errors="ignore") # if uninteresting_cols not in df, its okay
        dfs.append(df)
    df = pd.concat(dfs, axis=1)
    return df

def df_from_hdf5_with_filter_extraction(hdf5_file, 
                                        filter_names,
                                        filtermask_name = "OfflineFilterMask", 
                                        extra_cols = ["Run", "Event"]
                                       ):
    """ Split the table of filters into 'filter_cond', 'filter_pre', and 'filter' (both pass)
    
    Since filter mask in HDF5 is [cond, pre], can't convert using pd.DataFrame.from_records(table.read())
    
    Parameters
    ----------
    hdf5_file : file
        hdf5_file opened using tables.open_file(path, 'r')
    filtermask_name : str
        name of filter mask in hdf5 file.
    filter_names : list of str, otional
        list of filters to look for. default None will look automatically for filters by checking if col is 2D ([cond, pre]) 
    extra_cols : list of str, optional
        extra cols from filtermask table to be included, for example run/event info

    Returns
    -------
    pd.DataFrame
        Dataframe with filter mask split into cond, pre and both (default filter name)
    """
    
    filtergroup = hdf5_file.root[filtermask_name]
    filter_dict = {}
    for name in filter_names:
        filter_dict[name+"_cond"] = filtergroup.col(name)[:,0] # condition
        filter_dict[name+"_pre"] = filtergroup.col(name)[:,1] # prescale
        filter_dict[name] = np.logical_and(filtergroup.col(name)[:,0], filtergroup.col(name)[:,1]) # both
    for col in extra_cols: # extra info
        filter_dict[col] = filtergroup.col(col)
    # convert to df and return
    df_filter = pd.DataFrame(filter_dict)
    return df_filter


####################################################################################
########################### OPEN HDF5 -> DF ########################################
####################################################################################

# OPEN HDF5
online_hdf5 = tables.open_file(params['online'], 'r')
offline_hdf5 =  tables.open_file(params['offline'], 'r')
print(offline_hdf5)
# GET FILTER NAMES
filter_names = []
filtergroup = offline_hdf5.root[params["filtermask"]]
for col in filtergroup.colnames:
    # check if a column is 2D, if yes then assume it's a filter
    if len(filtergroup.col(col).shape) > 1: # is there a second dim?
        if filtergroup.col(col).shape[1] == 2: # is the second dim size 2?
            filter_names.append(col)
print("Colnames in filtermask:", filtergroup.colnames)
print("Filter names used:", filter_names)

##### OFFLINE24 HDF5 -> DF ##################
# {"filter":[condition, prescale]} -> {"filter":both, "filter_cond":condition, "filter_prescale":prescale} #####
df_filter = df_from_hdf5_with_filter_extraction(offline_hdf5, filtermask_name=params["filtermask"], filter_names=filter_names, extra_cols=["Run", "Event"])
offline_hdf5.close()

##### ONLINE HDF5 -> DF   ##################
uninteresting_cols = ["Run", "Event", "SubEvent", "SubEventStream", "exists"] # all tables have this
uninteresting_cols_dict = {
                        "LLPInfo": uninteresting_cols + ["interactions", "azimuth", "zenith"],
                        "MuonAtMMCBoundary": uninteresting_cols + ["N_track", "HighestMuonEnergy"],
                        "muongun_weights": uninteresting_cols,
                        "FilterMask": uninteresting_cols,
                        "I3EventHeader": ["SubEvent", "SubEventStream", "exists"],
                        }
interesting_tables = ["muongun_weights", "MuonAtMMCBoundary", "I3EventHeader", "LLPInfo"]
df_online = df_from_hdf(online_hdf5, interesting_tables, uninteresting_cols_dict)
df_online = df_online.rename(columns={"value": "weight"}) # muongun_weights is a table with column called 'value' as the weight
online_hdf5.close()

##### WHICH EVENTS PASS FILTERS? #####
# Create a set of (runID, eventID) from filtered file
event_ids = set(zip(df_filter['Run'], df_filter['Event']))
df_online['pass_filters'] = df_online.apply(lambda row: (row['Run'], row['Event']) in event_ids, axis=1)

# check which events pass filters, concat with filters df
df_offline = df_online[df_online['pass_filters']].reset_index(drop=True) # drop index to allow concat
df_offline = pd.concat([df_offline, df_filter], axis=1) # concat filters to df_offline

# sum of weights
online_tot_weight = sum(df_online["weight"])
offline_tot_weight = sum(df_offline["weight"])
print("Total weighted survival rate", offline_tot_weight/online_tot_weight)
##############################################

####################################################################################
########################### PLOT FILTERS ###########################################
####################################################################################

################ PLOT BAR CHARTS ################
folder = os.path.join(params["plot-folder"], "filter_barcharts/")
os.makedirs(folder, exist_ok=True)

def get_weighted_columns(df, colnames, weight_name="weight"):
    return df[colnames].multiply(df[weight_name], axis=0)
    
def get_frac(df, colnames, tot_weight, weight_name="weight"):
    weighted_columns = get_weighted_columns(df, colnames, weight_name="weight")
    weighted_frac = weighted_columns.sum()/tot_weight
    return weighted_frac

print("### ONLY CONDITION ###")
filter_names_condition = [name+"_cond" for name in filter_names]
frac = get_frac(df_offline, filter_names_condition, online_tot_weight)
plot_bar_chart(frac,
               'LLP survival rate online -> offline24 (only condition pass)',
               folder+"filter_condition_barchart.png",
               color="skyblue",
               ylog=False
              )
plot_bar_chart(frac,
               'LLP survival rate online -> offline24 (only condition pass)',
               folder+"filter_condition_barchart_log.png",
               color="skyblue",
               ylog=True
              )

print("### PRESCALE & CONDITION ###")
frac = get_frac(df_offline, filter_names, online_tot_weight)
plot_bar_chart(frac,
               'LLP survival rate online -> offline24',
               folder+"filter_barchart.png",
               ylog=False,
              )
plot_bar_chart(frac,
               'LLP survival rate online -> offline24',
               folder+"filter_barchart_log.png",
               ylog=True,
              )
plot_bar_chart(frac,
               'LLP survival rate online -> offline24',
               folder+"filter_barchart_drop_empty_log.png",
               ylog=True,
               drop_empty=True,
              )
plot_bar_chart(frac,
               'LLP survival rate online -> offline24',
               folder+"filter_barchart_drop_empty.png",
               ylog=False,
               drop_empty=True,
              )

##### PLOT ENERGY SPECTRUM ####
# cut out filters with less than cutoff survival rate
print("### SPECTRUM PLOTS ###")
frac = get_frac(df_offline, filter_names, online_tot_weight)
frac = frac.sort_values(ascending=False)
print("Total survival rate per filter", frac)
frac = frac[frac > params["cutoff"]]
print("Total survival rate per filter AFTER CUTOFF = {}".format(params["cutoff"]), frac)
filternames_survive = list(frac.index)
print("Name of filters after cutoff", filternames_survive)

# energy
colname = "TotalEnergy"
folder = os.path.join(params["plot-folder"], "filter_spectrum", colname)
xlabel = "Energy [GeV]"
plot_spectrum(df_offline, df_online, filternames_survive, colname, online_tot_weight, folder, xlabel=xlabel, xlog=True, ylog=True, ybottom=1e-5, title="LLP MC: Online -> Offline")

# gap
colname = "length"
folder = os.path.join(params["plot-folder"], "filter_spectrum/gap_length/")
xlabel = "Gap Length [m]"
plot_spectrum(df_offline, df_online, filternames_survive, colname, online_tot_weight, folder, xlabel=xlabel, xlog=False, ylog=True, ybottom=1e-5, xmax=700, title="LLP MC: Online -> Offline")

##### PLOT RATIOS #####
# TOTAL ENERGY  
colname="TotalEnergy"
path= os.path.join(params["plot-folder"], "ratio/"+colname+"/all_filter_ratio_plot.png")
os.makedirs(os.path.dirname(path), exist_ok=True)
bins=50
logbins = np.geomspace(df_online[colname].min(), df_online[colname].max(), bins)

# plot all filter ratio enery
ratio_plot(df_online, df_offline, colname, logbins, path, title="LLP Survival rate online -> offline24", xlabel="Energy [GeV]")

# plot each filter ratio
for filtername in filternames_survive:
    df_filtered = df_offline[df_offline[filtername]]
    path=os.path.join(params["plot-folder"], "ratio/"+colname+"/"+filtername+"_ratio_plot.png")
    ratio_plot(df_online, df_filtered, colname, logbins, path, label1="Online", label2=filtername,
              title=filtername, xlabel="Energy [GeV]")

# GAP LENGTH
colname="length"
path= os.path.join(params["plot-folder"], "ratio/gap_length/all_filter_ratio_plot.png")
os.makedirs(os.path.dirname(path), exist_ok=True)
bins=50
logbins = np.geomspace(df_online[colname].min(), df_online[colname].max(), bins)

# plot all filter ratio gap length
ratio_plot(df_online, df_offline, colname, logbins, path, title="LLP Survival rate online -> offline24", xlabel="Gap Length [m]",
          color1="orange", color2="purple")

# plot each filter ratio gap length
for filtername in filternames_survive:
    df_filtered = df_offline[df_offline[filtername]]
    path=os.path.join(params["plot-folder"], "/ratio/gap_length/"+filtername+"_ratio_plot.png")
    ratio_plot(df_online, df_filtered, colname, logbins, path, label1="Online", label2=filtername,
              title=filtername, xlabel="Gap Length [m]", color1="orange", color2="purple")

##### PLOT ALL RATIOS ON THE SAME PLOT, ENERGY ######
colname = "TotalEnergy"
path= os.path.join(params["plot-folder"], "ratio/TotalEnergy/only_ratios.png")
logbins = np.geomspace(df_online[colname].min(), df_online[colname].max(), bins)
plt.figure()
for filtername in filternames_survive:
    df_filtered = df_offline[df_offline[filtername]]
    ratios, bin_centers = get_ratios(df_online, df_filtered, colname, logbins)
    plt.plot(bin_centers, ratios, label=filtername)
plt.legend()
plt.xscale("log")
plt.xlabel("Energy [GeV]")
plt.ylabel("Binned survival ratio")
plt.title("Binned survival ratio online to offline24")
plt.savefig(path)

##### PLOT ALL RATIOS ON THE SAME PLOT, GAP LENGTH ######
colname = "length"
path= os.path.join(params["plot-folder"], "ratio/gap_length/only_ratios.png")
logbins = np.geomspace(df_online[colname].min(), df_online[colname].max(), bins)
plt.figure()
for filtername in filternames_survive:
    df_filtered = df_offline[df_offline[filtername]]
    ratios, bin_centers = get_ratios(df_online, df_filtered, colname, logbins)
    plt.plot(bin_centers, ratios, label=filtername)
plt.legend()
plt.xscale("log")
plt.xlabel("Gap Length [m]")
plt.ylabel("Binned survival ratio")
plt.title("Binned survival ratio online to offline24")
plt.savefig(path)
