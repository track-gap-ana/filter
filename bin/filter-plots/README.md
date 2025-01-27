Plot online vs offline. `plot_filter_plots.py` takes in two hdf5 files (online/offline) and plots stuff pre/post filer. Plot functions found in `plot_functions.py`. Example bash run script is `example_run_plot_filter_plots.sh`.

These hdf5 files are preferrably created using the `event_selection` package (https://github.com/track-gap-ana/event-selection/tree/main), particularly https://github.com/track-gap-ana/event-selection/blob/main/scripts/analysis-datasets/create_hdf5_files.py

Online .hdf5 needs the following tables `["muongun_weights", "MuonAtMMCBoundary", "I3EventHeader", "LLPInfo"]` ("MuonAtMMCBoundary" is a frame object created by https://github.com/track-gap-ana/event-selection/blob/main/src/event_selection/processing/utils.py#L82 as a way to serialize `MMCTrackList`. It contains ["HighestMuonEnergy", "TotalEnergy", "N_track"]).

Offline .hdf5 needs the table specified by `--filtermask`.