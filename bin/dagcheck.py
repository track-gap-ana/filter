""" Check for corrupt files etc. in the simulation set. """

import argparse
import glob
import os
from icecube import icetray, dataio

def compile_bad_files(folder):
    # check for backslash
    if folder[-1] != '/':
        folder += '/'
    print("Checking folder:", folder)

    # files
    filelist = glob.glob(folder + '*.i3.gz')
    print("Folder contains %i files." % len(filelist))

    # check read access
    for f in filelist:
        if not os.access(f, os.R_OK):
            raise Exception('Cannot read from %s' % f)

    # check each file
    badfiles = []
    print("Start checking files:")
    for i, file in enumerate(filelist):
        frame_counter = {}
        with dataio.I3File(file) as f:
            while f.more():
                try:
                    frame = f.pop_frame()
                except:
                    print("Error popping frame in file ", file)
                    print("Current frame_counter:", frame_counter)
                    print("Moving to next file!")
                    badfiles.append(file)
                    break  # move to next file
                stop = frame.Stop.id
                if stop in frame_counter:
                    frame_counter[stop] += 1
                else:
                    frame_counter[stop] = 1
            print("Checked file ", i, " with frames:", frame_counter)

    return badfiles

def write_bad_files(badfiles, bad_files_path):
    print("Writing bad file list to ", bad_files_path)
    with open(bad_files_path, "w") as f:
        for b in badfiles:
            f.write(b + "\n")
    return bad_files_path

def remove_bad_files(badfiles):
    for f in badfiles:
        # Check if the file exists before trying to delete it
        if os.path.exists(f):
            os.remove(f)
            print(f"The file {f} has been deleted successfully.")
        else:
            print(f"The file {f} does not exist.")

def main():
    parser = argparse.ArgumentParser(description='Check for corrupt files in the simulation set.')
    parser.add_argument('-f', '--folder', type=str, help='Path to the folder containing the simulations')
    parser.add_argument('--remove-bad', dest="remove_bad", action='store_true', default=False, help='Remove bad files?')

    args = parser.parse_args()
    if args.folder:
        bad_files_path = os.path.join(args.folder, "bad_files.txt")
        print("Bad files will be written to ", bad_files_path)
        if args.remove_bad:
            if os.path.exists(bad_files_path):
                print("Reading bad files from ", bad_files_path)
                with open(bad_files_path, "r") as f:
                    badfiles = [line.strip() for line in f.readlines()]
            else:
                print("Bad files have not yet been written. Writing list of bad files and removing them.")
                badfiles = compile_bad_files(args.folder)
                write_bad_files(badfiles, bad_files_path)
            remove_bad_files(badfiles)
        else:
            badfiles = compile_bad_files(args.folder)
            write_bad_files(badfiles, bad_files_path)

if __name__ == "__main__":
    main()