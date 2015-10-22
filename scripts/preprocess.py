#!/usr/bin/env python
import os
import argparse as ap
import re
import xml.etree.ElementTree as et
import sys
import datetime
import matplotlib.pyplot as plt
import numpy as np
import wave

def getfiles(path):
    """
    Gets the file names in a directory.
    """
    f = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        f.extend(filenames)
        break;
    return f


def glass(path):
    """
    Apply preprocessing to Google Glass data.
    """
    # Get list of files in Glass directory.
    glasspath = "./" + path + "/glass"
    files = getfiles(glasspath)
    # Filter and sort list for Glass data.
    regex = re.compile('\AIMUData_.*\.txt$')
    files = sorted([m.group(0) for l in files for m in [regex.search(l)] if m])
    # Initialize loop variables.
    keys = ['Gyroscope', 'Accelerometer', 'MagneticField', 'EulerAngles', 'RotationVector']
    # keys = ['Gyroscope', 'Accelerometer', 'MagneticField']
    template  = dict( (k, []) for k in keys )  # Because python sucks. :C
    abstime   = dict( (k, []) for k in keys )
    reltime   = dict( (k, []) for k in keys )
    xyz       = dict( (k, []) for k in keys )
    starttime = dict( (k, None) for k in keys )
    # For each file... FIXME There should only be one file?
    for f in files:
        glassfname = glasspath + "/" + f
        with open(glassfname, 'r') as glassfile:
            for line in glassfile:
                # Split the line into it's fields.
                line = line.strip()
                tokens = line.split(' ')
                # Check for truncation at EOF.
                if len(tokens) < 8:
                    break
                # Check if token zero is in accepted keys.
                k = tokens[0]
                if k in keys:
                    # Convert timestamps to datetime.
                    try:
                        t1text = " ".join([tokens[1], tokens[2]])
                        t1 = datetime.datetime.strptime(t1text, '%Y-%m-%d %H:%M:%S.%f')
                        t2text = " ".join([tokens[3], tokens[4]])
                        t2 = datetime.datetime.strptime(t2text, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:  # Catch truncated line before EOF.
                        break
                    # Pick one as current time.
                    curtime = t2;
                    timetext = t2text;
                    # Record the start time on first pass through.
                    if not starttime[k]:
                        starttime[k] = curtime
                    # Record the absolutime timestamp.
                    abstime[k].append(timetext)
                    # Record the relative timestamp.
                    delta = (curtime - starttime[k]).total_seconds()
                    reltime[k].append(delta)
                    # Record the XYZ.
                    xyz[k].append(", ".join(tokens[5:]))

    # Glass files.
    fnames = dict()
    fnames['Gyroscope']      = 'ggyro.csv'
    fnames['Accelerometer']  = 'gaccel.csv'
    fnames['MagneticField']  = 'gmag.csv'
    fnames['EulerAngles']    = 'geuler.csv'
    fnames['RotationVector'] = 'grvec.csv'
    # Output to csv.
    outpath = path + "/datafiles/"
    for k in keys:
        # Build file name.
        outfname = outpath + fnames[k]
        print "Writing to", outfname
        # Check if the path exists and create if necessary.
        outdir = os.path.dirname(outfname)
        try:
            os.stat(outdir)
        except:
            os.mkdir(outdir)
        # Convert to numpy.
        reltime[k] = np.array(reltime[k])
        # Open Glass data file.
        with open(outfname, 'w') as outfile:
            # Write data.
            for i in range(len(reltime[k])):
                outfile.write(abstime[k][i])
                outfile.write(", ")
                outfile.write(str(reltime[k][i]))
                outfile.write(", ")
                outfile.write(str(xyz[k][i]))
                outfile.write("\n")


def pebble(path):
    """
    Apply preprocessing to Pebble data.
    """
    # Get list of files in Pebble directory.
    pebble_path = "./" + path + "/pebble/"
    files = getfiles(pebble_path)
    # Filter and sort list for wrist accel data.
    regex = re.compile('\A[0-9]{1}-waccel.*')
    files0 = sorted([m.group(0) for l in files for m in [regex.search(l)] if m])
    regex = re.compile('\A[0-9]{2}-waccel.*')
    files1 = sorted([m.group(0) for l in files for m in [regex.search(l)] if m])
    files = files0 + files1
    # Initialize loop variables.
    newline = ""
    start = None
    abstime = []
    reltime = []
    xyz = [[],[],[]]
    i = 0
    prev_time = datetime.datetime.today()

    # For each file...
    for f in files:
        tree = et.parse(pebble_path + f)
        root = tree.getroot()
        for child in root.iter():
            if child.tag == "string":
                # Zero fill the milliseconds on the left. strptime misinterprets
                # ":98" as .98 seconds instead of .098 seconds.
                tokens = child.text.split(":")
                tokens[-1] = tokens[-1].zfill(3)
                text = ":".join(tokens)
                # Pebble sometimes fails to carry the second when incrementing
                # from .999 seconds to 1.000 seconds. Here we detect and fix
                # this error.
                curr_time = datetime.datetime.strptime(text, '%Y/%m/%d %H:%M:%S:%f')
                if (prev_time.microsecond >= 999 and curr_time.microsecond == 0 and
                    prev_time.second == curr_time.second):
                    # Carry the one.
                    s = (curr_time.second + 1) % 60
                    m = curr_time.minute + (curr_time.second + 1) / 60
                    curr_time = curr_time.replace(minute=m, second=s)
                # Store previous time for next iteration.
                prev_time = curr_time
                # Record the start time on the first pass through.
                if start == None:
                    start = curr_time
                # Record the delta time from the start and the absolute time.
                delta = (curr_time - start).total_seconds()
                reltime.append(delta)
                abstime.append(text)
            if child.tag == "integer":
                # Record the accelerometer readings.
                xyz[i].append(child.text)
                i = (i + 1)%3

    # Convert lists to numpy arrays.
    reltime = np.array(reltime)
    xyz[0] = np.array(xyz[0])
    xyz[1] = np.array(xyz[1])
    xyz[2] = np.array(xyz[2])

    # TODO Sanity checks monotonic time.

    # Backwards algorithm for computing relative time. This method appears to
    # work better than other approaches like computing a relative time using an
    # estimated frequency or using the raw relative time.
    # Verification:
    #   number samples: 37725
    #   total time:     1555.384
    #   expect samples: 38884.6
    #   delta expected: 1159.6
    #   lost samples:   403.743000001
    bcktime = np.zeros(len(reltime), dtype=np.float64)
    bt = reltime[-1]
    # Loop backwards over indices.
    for i in range(len(reltime)-1, -1, -1):
        # If the estimated time isn't keeping up with the timestamp, jump
        # backwards to catch up.
        if reltime[i] < bt:
            bt = reltime[i]
        bcktime[i] = bt
        bt = bt - (1.0/25)
    # dbt = bcktime[1:] - bcktime[0:len(bcktime)-1]
    # plt.plot(dbt, '+')
    # plt.show()

    # TODO Smoothing.

    # Pebble data filename.
    outfname = path + "/datafiles/waccel.csv"
    print "Writing to", outfname
    # Check if the path exists and create if necessary.
    outdir = os.path.dirname(outfname)
    try:
        os.stat(outdir)
    except:
        os.mkdir(outdir)
    # Open Pebble data file.
    with open(outfname, 'w') as outfile:
        # Write data.
        for i in range(len(reltime)):
            outfile.write(abstime[i])
            outfile.write(", ")
            outfile.write(str(bcktime[i]))
            for j in range(3):
                outfile.write(", " + str(xyz[j][i]))
            outfile.write("\n")


def olympus(path):
    """
    Apply preprocessing to Olympus data.
    """
    # Get list of files in Olympus directory.
    olympus_path = "./" + path + "/olympus/"
    files = getfiles(olympus_path)
    # Filter and sort list for head microphone data.
    regex = re.compile('\ADD.*\.wav$')
    files = sorted([m.group(0) for l in files for m in [regex.search(l)] if m])
    # Open the file. FIXME Should only be one file.
    signal = None
    hz = 0
    for f in files:
        wavfile = wave.open(olympus_path + f, 'r')
        hz = np.float64(wavfile.getframerate())
        # Just mono files.
        assert wavfile.getnchannels() == 1
        signal = wavfile.readframes(16000 * 100)
        signal = np.fromstring(signal, 'Int16')

    # Write data to csv.
    outfname = path + "/datafiles/hmic.csv"
    print "Writing to", outfname
    # Check if the path exists and create if necessary.
    outdir = os.path.dirname(outfname)
    try:
        os.stat(outdir)
    except:
        os.mkdir(outdir)
    # Open data file.
    with open(outfname, 'w') as outfile:
        # Write data.
        for i in range(len(signal)):
            outfile.write('%.8f' % (i / hz))
            outfile.write(", ")
            outfile.write(str(signal[i]))
            outfile.write("\n")


def sony(path):
    """
    Apply preprocessing to Sony data.
    """
    # Get list of files in Sony directory.
    sony_path = "./" + path + "/sony/"
    files = getfiles(sony_path)
    # Filter and sort list for head microphone data.
    regex = re.compile('.*\.wav$')
    files = sorted([m.group(0) for l in files for m in [regex.search(l)] if m])
    # Open the file. FIXME Should only be one file.
    signal = None
    hz = 0
    for f in files:
        wavfile = wave.open(sony_path + f, 'r')
        hz = np.float64(wavfile.getframerate())
        # Just mono files.
        assert wavfile.getnchannels() == 1
        signal = wavfile.readframes(16000 * 100)
        signal = np.fromstring(signal, 'Int16')

    # Write data to csv.
    outfname = path + "/datafiles/wmic.csv"
    print "Writing to", outfname
    # Check if the path exists and create if necessary.
    outdir = os.path.dirname(outfname)
    try:
        os.stat(outdir)
    except:
        os.mkdir(outdir)
    # Open data file.
    with open(outfname, 'w') as outfile:
        # Write data.
        for i in range(len(signal)):
            outfile.write('%.8f' % (i / hz))
            outfile.write(", ")
            outfile.write(str(signal[i]))
            outfile.write("\n")


def main():
    parser = ap.ArgumentParser(description='Eating session proprocessor')
    parser.add_argument('fpath', metavar='<path>', help='Path to session data')
    args = parser.parse_args()

    glass(args.fpath)
    pebble(args.fpath)
    olympus(args.fpath)
    sony(args.fpath)

if __name__ == "__main__":
    main()
