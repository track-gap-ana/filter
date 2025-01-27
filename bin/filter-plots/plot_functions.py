""" Functions used to plot ratios, spectra etc. for pre/post filter. """
import numpy as np
import matplotlib.pyplot as plt
import os

def plot_bar_chart(frac, title, path, color="blue", ylim=None, drop_empty=False, ylog=False):
    """ Total survival ratio bar chart"""
    plt.figure()
    if drop_empty:
        frac = frac[frac > 0.0]
    frac.plot(kind='bar', color=color, figsize=(8, 6)) # bar chart the fractions
    plt.title(title)
    plt.ylabel('Weighted survival rate')
    plt.xticks(rotation=90, ha='right')
    if ylog:
        plt.yscale("log")
    elif ylim is not None:
        plt.ylim(ylim)
    plt.tight_layout()
    plt.savefig(path)

def plot_energy_fractions(df, colname, filtername,
                          tot_weight, 
                          path,
                          xlabel=None,
                          weight_name="weight", 
                          xlog=True, ylog=True,
                          ybottom=None,
                          xmax=None,
                          title=None,
                         ):
    """ Survival of single filter """
    df_filtered = df[df[filtername]]
    plt.figure()
    bins = 50
    if xlog:
        plt.xscale("log")
        bins = np.logspace(np.log10(df_filtered[colname].min()),np.log10(df_filtered[colname].max()),bins)
    plt.hist(df_filtered[colname], weights=df_filtered[weight_name]/tot_weight, bins=bins)
    if ylog:
        plt.yscale("log")
    if title is None:
        title = filtername
        plt.title(filtername)
    plt.ylabel("Binned survival rate")
    if xlabel is None:
        xlabel = colname
    if ybottom is not None:
        plt.gca().set_ylim(bottom=ybottom)
    if xmax is not None:
        plt.gca().set_xlim(right=xmax)
    plt.xlabel(xlabel)
    plt.savefig(path)
    plt.close()

def plot_all_filters_spectrum(df, df_pre, colname, filternames,
                          tot_weight, 
                          path,
                          xlabel=None,
                          weight_name="weight", 
                          xlog=True,
                          ylog=True,
                          ybottom=None,
                          title=None,
                          xmax=None
                         ):
    """ Survival of all filters on one plot """
    plt.figure(figsize=(10,6))
    bins = 50
    if xlog:
        plt.xscale("log")
        bins = np.logspace(np.log10(df[colname].min()),np.log10(df[colname].max()),bins)
    plt.hist(df_pre[colname], weights=df_pre[weight_name]/tot_weight,
            label="Online",
            alpha=0.8,
            bins=bins,
            histtype="stepfilled",
            edgecolor="black",
            )
    for filtername in filternames:
        df_filtered = df[df[filtername]]
        plt.hist(df_filtered[colname], weights=df_filtered[weight_name]/tot_weight,
                label=filtername,
                alpha=0.8,
                bins=bins,
                histtype="stepfilled",
                edgecolor="black",
                )
    if ylog:
        plt.yscale("log")
    if ybottom is not None:
        plt.gca().set_ylim(bottom=ybottom)
    if xmax is not None:
        plt.gca().set_xlim(right=xmax)
    plt.ylabel("Binned survival rate")
    if xlabel is None:
        xlabel = colname
    if title is not None:
        plt.title(title)
    plt.xlabel(xlabel)
    plt.legend()
    plt.savefig(path)
    plt.close()


def plot_spectrum(df, df_pre, filternames, colname, tot_weight, folder, **kwargs):
    """ Plot the energy spectrum for each filter and all filters at once.
    Calls plot_energy_fractions() and plot_all_filters_spectrum()
    """
    os.makedirs(folder, exist_ok=True)
    for filtername in filternames:
        kwargs_0 = dict(kwargs)
        kwargs_0.pop('title', None) # title in kwargs if for all filters, not here
        path = os.path.join(folder, filtername + "_" + colname + ".png")
        plot_energy_fractions(df, colname, filtername,
                              tot_weight,
                              path,
                              title=filtername,
                              **kwargs_0
                             )
    # all filters at once
    path = os.path.join(folder, "all_filters_"+colname+".png")
    plot_all_filters_spectrum(df, df_pre, colname, filternames,
                              tot_weight, 
                              path,
                              **kwargs,
                             )

########### RATIO PLOTS ############
# create bins
def get_ratios(df1, df2, colname, bins, weight_name="weight"):
    hist1, bin_edges = np.histogram(df1[colname], bins = bins, weights=df1[weight_name])
    hist2, bin_edges = np.histogram(df2[colname], bins = bins, weights=df2[weight_name])
    ratios = [x/y if y != 0 else 0 for x,y in zip(hist2, hist1)]
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    return ratios, bin_centers
    
def ratio_plot(df1, df2, colname, bins, path, weight_name="weight", label1="Online", label2="Offline", title=None, xlabel=None,
              color1=None, color2=None):
    ratios, bin_centers = get_ratios(df1, df2, colname, bins)

    if color1 is None:
        color1="navy"
    if color2 is None:
        color2="firebrick"
    
    # combined ratio and count plot
    fig, ax1 = plt.subplots(figsize=(10,6))
    ax1.hist(df1[colname], bins = bins, alpha=0.8, 
             label=label1, color = color1,
             weights=df1[weight_name])
    ax1.hist(df2[colname], bins = bins, alpha=0.8, 
             label = label2, color = color2, 
             weights=df2[weight_name])
    ax1.loglog()
    if xlabel is None:
        xlabel=colname
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel("Weighted relative count")
    
    ax2 = ax1.twinx()
    ax2.plot(bin_centers, ratios, "o-", color="black", label="ratio")
    ax2.set_ylabel("Ratio Online/Offline")
    
    # ask matplotlib for the plotted objects and their labels
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc=0)
    plt.title(title)
    plt.savefig(path)
    plt.close()
