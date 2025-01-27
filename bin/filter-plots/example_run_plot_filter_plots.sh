online_path="/data/user/axelpo/analysis-datasets/sig/compare_online_offline24_215984659/online_sig.hdf5"
offline_path="/data/user/axelpo/analysis-datasets/sig/compare_online_offline24_215984659/offline24_sig.hdf5"

setname="online_offline24_215984659_50m_mingap"
plotfolder="comparison_plots/"+$setname+"/"
cutoff=0.0 # all filters
filtermask="OfflineFilterMask"

python filter_plots.py \
    --online $online_path \
    --offline $offline_path \
    --plot-folder $plotfolder \
    --cutoff $cutoff \
    --filtermask $filtermask \