import csv
import sys
import numpy as np
from numpy import sin, linspace, pi
from pylab import plot, show, title, xlabel, ylabel, subplot, figure
from scipy import fft, arange
from copy import copy
from random import randint
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from scipy.io import wavfile
import random
import yaafelib as yaafe
yaafe.loadComponentLibrary('yaafe-io')

#old_settings = np.seterr(all='raise')

def getdata(directory, sessions):
    data = []
    offsets = []
    annotations = []
    files =['gaccel.csv', 'waccel.csv']
    device = ['gaccel', 'waccel']
    print "Offsets"
    with open(directory+'/offsets.txt') as offsets_file:
        readfile = csv.reader(offsets_file, delimiter=' ')
        rowi = 0
        for row in readfile:
            offsets.append({})
            offsets[rowi]['waccel'] = float(row[0].strip())
            offsets[rowi]['gaccel'] = float(row[1].strip())
            offsets[rowi]['hmic'] = float(row[3].strip())
            offsets[rowi]['wmic'] = float(row[4].strip())
            rowi += 1
    print "Devices"        
    for i in range(len(sessions)):
        print sessions[i]
        annotations.append([[], []])
        with open(directory+'/'+sessions[i]+'/annotations.csv', 'rb') as csvfile:
            rowi = 0
            readfile = csv.reader(csvfile, delimiter=',')
            for row in readfile:
                if rowi > 0:
                    min = float(row[0].strip().split(':')[0])
                    sec = float(row[0].strip().split(':')[1])
                    annotations[i][int(row[2].strip())-1].append(60.*min+sec)
                rowi += 1
                
        data.append({})
        for j in range(len(files)):
            with open(directory+'/'+sessions[i]+'/datafiles/'+files[j], 'rb') as csvfile:
                data[i][device[j]+'_z'] = []
                data[i][device[j]+'_y'] = []
                data[i][device[j]+'_x'] = []
                readfile = csv.reader(csvfile, delimiter=',')
                for row in readfile:
                    data[i][device[j]+'_z'].append(float(row[2].strip()))
                    data[i][device[j]+'_y'].append(float(row[3].strip()))
                    data[i][device[j]+'_x'].append(float(row[4].strip()))
                    
    afiles = ['olympus/head.wav', 'sony/wrist.wav']
    adevice = ['hmic', 'wmic']
    print "Audio"
    for i in range(len(sessions)):
        print sessions[i]
        for j in range(len(afiles)):
            file = directory+'/'+sessions[i]+'/'+afiles[j]
            fs, adata = wavfile.read(file)
            data[i][adevice[j]] = adata
            
    return offsets, annotations, data

def getfft(y,Fs):
    y = list(y)
    zeropadding = [0]*10000
    y = y + zeropadding
    n = len(y) # length of the signal
    k = arange(n, dtype=float)
    T = n/Fs
    frq = k/T # two sides frequency range
    frq = frq[range(n/2)] # one side frequency range
    Y = fft(y)/n # fft computing and normalization
    Y = Y[range(n/2)]
    #print type(frq[0])
    return frq, list(abs(Y))

def genframes(offsets, annotations, data, sampling, glass=True, pebble=True, hmic=True, wmic=True, framelen=5):
    eating = []
    noneating = []
    for i in range(len(data)):
        maxo = max(offsets[i].values())
        eat1start = annotations[i][0][0]
        eat1end = annotations[i][0][-1]
        eat2start = annotations[i][1][0]
        eat2end = annotations[i][1][-1]
        noneat1start = maxo
        noneat1end = eat1start - framelen
        noneat2start = eat1end + 2*framelen
        noneat2end = eat2start - framelen
        neatsamples1 = len(annotations[i][0])
        neatsamples2 = len(annotations[i][1])
        neatsamples = neatsamples1 + neatsamples2
        nnoneatsamples1 = int((noneat1end - noneat1start)/framelen)
        nnoneatsamples2 = int((noneat2end - noneat2start)/framelen)
        nnoneatsamples = nnoneatsamples1 + nnoneatsamples2
        eating.append([[] for j in range(neatsamples)])
        noneating.append([[] for j in range(nnoneatsamples)])
        print neatsamples1, neatsamples2, nnoneatsamples1, nnoneatsamples2
        if glass == True:
            for j in range(neatsamples):
                if j < neatsamples1:
                    k = 0
                    l = j
                else:
                    k = 1
                    l = j-neatsamples1
                start = int((annotations[i][k][l]-2-offsets[i]['gaccel'])*sampling['gaccel'])
                stop = start + framelen*sampling['gaccel']
                x = data[i]['gaccel_x'][start:stop]
                y = data[i]['gaccel_y'][start:stop]
                z = data[i]['gaccel_z'][start:stop]
                
                frqx, X = getfft(x, sampling['gaccel'])
                frqy, Y = getfft(y, sampling['gaccel'])
                frqz, Z = getfft(z, sampling['gaccel'])
                for m in range(10):
                    X[m] = 0.
                    Y[m] = 0.
                    Z[m] = 0.
                frq1x = frqx[X.index(max(X))]
                X[X.index(max(X))] = 0
                frq2x = frqx[X.index(max(X))]
                frq1y = frqy[Y.index(max(Y))]
                Y[Y.index(max(Y))] = 0
                frq2y = frqy[Y.index(max(Y))]
                frq1z = frqz[Z.index(max(Z))]
                Z[Z.index(max(Z))] = 0
                frq2z = frqz[Z.index(max(Z))]
                
                eating[i][j].extend([np.mean(x), np.mean(y), np.mean(z), np.std(x), np.std(y), np.std(z), frq1x, frq2x, frq1y, frq2y, frq1z, frq2z])
                
            for j in range(nnoneatsamples):
                if j < nnoneatsamples1:
                    offset = int((noneat1start - offsets[i]['gaccel'])*sampling['gaccel'])
                    l = j
                else:
                    offset = int((noneat2start - offsets[i]['gaccel'])*sampling['gaccel'])
                    l = j-nnoneatsamples1
                start = offset + l*sampling['gaccel']
                stop = start + framelen*sampling['gaccel']
                x = data[i]['gaccel_x'][start:stop]
                y = data[i]['gaccel_y'][start:stop]
                z = data[i]['gaccel_z'][start:stop]
                
                frqx, X = getfft(x, sampling['gaccel'])
                frqy, Y = getfft(y, sampling['gaccel'])
                frqz, Z = getfft(z, sampling['gaccel'])
                for m in range(10):
                    X[m] = 0.
                    Y[m] = 0.
                    Z[m] = 0.
                frq1x = frqx[X.index(max(X))]
                X[X.index(max(X))] = 0
                frq2x = frqx[X.index(max(X))]
                frq1y = frqy[Y.index(max(Y))]
                Y[Y.index(max(Y))] = 0
                frq2y = frqy[Y.index(max(Y))]
                frq1z = frqz[Z.index(max(Z))]
                Z[Z.index(max(Z))] = 0
                frq2z = frqz[Z.index(max(Z))]
                
                noneating[i][j].extend([np.mean(x), np.mean(y), np.mean(z), np.std(x), np.std(y), np.std(z), frq1x, frq2x, frq1y, frq2y, frq1z, frq2z])
                
        if pebble == True:
            for j in range(neatsamples):
                if j < neatsamples1:
                    k = 0
                    l = j
                else:
                    k = 1
                    l = j-neatsamples1
                start = int((annotations[i][k][l]-2-offsets[i]['waccel'])*sampling['waccel'])
                stop = start + framelen*sampling['waccel']
                x = data[i]['waccel_x'][start:stop]
                y = data[i]['waccel_y'][start:stop]
                z = data[i]['waccel_z'][start:stop]
                
                
                eating[i][j].extend([x[z.index(max(z))], y[z.index(max(z))], max(z), np.mean(x), np.mean(y), np.mean(z), np.std(x), np.std(y), np.std(z)])
                
            for j in range(nnoneatsamples):
                if j < nnoneatsamples1:
                    offset = int((noneat1start - offsets[i]['waccel'])*sampling['waccel'])
                    l = j
                else:
                    offset = int((noneat2start - offsets[i]['waccel'])*sampling['waccel'])
                    l = j-nnoneatsamples1
                start = offset + l*sampling['waccel']
                stop = start + framelen*sampling['waccel']
                x = data[i]['waccel_x'][start:stop]
                y = data[i]['waccel_y'][start:stop]
                z = data[i]['waccel_z'][start:stop]
                
                noneating[i][j].extend([x[z.index(max(z))], y[z.index(max(z))], max(z), np.mean(x), np.mean(y), np.mean(z), np.std(x), np.std(y), np.std(z)])
                
        dev = ['hmic', 'wmic']
        devflag = [hmic, wmic]
        features = ['ZCR', 'AmplitudeModulation', 'SpectralRolloff', 'Loudness', 'Energy', 'EnvelopeShapeStatistics', 'SpectralShapeStatistics', 'TemporalShapeStatistics']
        for m in range(len(dev)):
            if devflag[m] == True:
                for j in range(neatsamples):
                    print 'eat', j, neatsamples
                    if j < neatsamples1:
                        k = 0
                        l = j
                    else:
                        k = 1
                        l = j-neatsamples1
                    start = int((annotations[i][k][l]-2-offsets[i][dev[m]])*sampling[dev[m]])
                    stop = start + framelen*sampling[dev[m]]
                    f = data[i][dev[m]][start:stop]
                    print len(f)
                    wavfile.write('temp.wav', sampling[dev[m]], f)
                    
                    for feature in features:
                        fp = yaafe.FeaturePlan(sample_rate=sampling[dev[m]],
                               normalize=None,
                               resample=False)
                        fp.addFeature('feat: '+feature+' blockSize='+str(len(f))+' stepSize='+str(len(f)))
                        engine = yaafe.Engine()
                        engine.load(fp.getDataFlow())

                        afp = yaafe.AudioFileProcessor()
                        afp.setOutputFormat("csv","", {'Metadata':'False'})
                        afp.processFile(engine,'temp.wav')
                        del fp
                        del engine
                        del afp
                        with open('temp.wav.feat.csv') as csvfile:
                            readfile = csv.reader(csvfile, delimiter=',')
                            for row in readfile:
                                eating[i][j].extend([float(row[n]) for n in range(len(row))])
                        csvfile.close()
                    
                for j in range(nnoneatsamples):
                    print 'noneat', j, nnoneatsamples
                    if j < nnoneatsamples1:
                        offset = int((noneat1start - offsets[i][dev[m]])*sampling[dev[m]])
                        l = j
                    else:
                        offset = int((noneat2start - offsets[i][dev[m]])*sampling[dev[m]])
                        l = j-nnoneatsamples1
                    start = offset + l*sampling[dev[m]]
                    stop = start + framelen*sampling[dev[m]]
                    f = data[i][dev[m]][start:stop]
                    wavfile.write('temp.wav', sampling[dev[m]], f)
                    
                    for feature in features:
                        fp = yaafe.FeaturePlan(sample_rate=sampling['hmic'],
                               normalize=None,
                               resample=False)
                        fp.addFeature('feat: '+feature+' blockSize='+str(len(f))+' stepSize='+str(len(f)))
                        engine = yaafe.Engine()
                        engine.load(fp.getDataFlow())
                        
                        afp = yaafe.AudioFileProcessor()
                        afp.setOutputFormat("csv","", {'Metadata':'False'})
                        afp.processFile(engine,'temp.wav')
                        
                        with open('temp.wav.feat.csv') as csvfile:
                            readfile = csv.reader(csvfile, delimiter=',')
                            for row in readfile:
                                noneating[i][j].extend([float(row[n]) for n in range(len(row))])
                        csvfile.close()
                    
    return eating, noneating
    
def getframes(directory, sessions, nframes, glass = True, pebble = True, hmic = True, wmic = True):
    eating = []
    noneating = []
    for i in range(len(sessions)):
        eating.append([[] for j in range(nframes[i])])
        noneating.append([[] for j in range(nframes[i])])
        dev = ['glass', 'pebble', 'hmic', 'wmic']
        devflag = [glass, pebble, hmic, wmic]
        for d in range(len(dev)):
            if devflag[d] == True:
                with open(directory+'/'+sessions[i]+'/feat_eating_'+dev[d]+'.csv') as csvfile:
                    readfile = csv.reader(csvfile, delimiter=',')
                    rowi = 0
                    for row in readfile:
                        eating[i][rowi].extend([float(row[j]) for j in range(len(row))])
                        rowi += 1
                        #if rowi == nframes[i]:
                            #break
                        
                #with open(directory+'/'+sessions[i]+'/feat_noneating_'+dev[d]+'.csv') as csvfile:
                    #print directory+'/'+sessions[i]+'/feat_noneating_'+dev[d]+'.csv'
                    #readfile = csv.reader(csvfile, delimiter=',')
                    #rowi = 0
                    #frames = 0
                    #for row in readfile:
                        ##if rowi > 100:
                        #print rowi
                        #noneating[i][frames].extend([float(row[j]) for j in range(len(row))])
                        #frames += 1
                        #rowi += 1
                        #if frames == nframes[i]:
                            #break
                
                rows = []
                with open(directory+'/'+sessions[i]+'/feat_noneating_'+dev[d]+'.csv') as csvfile:
                    readfile = csv.reader(csvfile, delimiter=',')
                    for row in readfile:
                        rows.append(row)
                    noneatsamples = random.sample(range(len(rows)), nframes[i])
                    for j in range(nframes[i]):
                        row = rows[noneatsamples[j]]
                        noneating[i][j].extend([float(row[k]) for k in range(len(row))])
                        
    return eating, noneating
    
directory = 'Data'
sessions = ['02', '03', '04']
nframes = [26, 53, 41]
runs = 10
totalcorrect = 0.
totalpredicted = 0.
total = 0.

for run in range(runs):
    eating, noneating = getframes(directory, sessions, nframes, glass = True, pebble = True, hmic = True, wmic = True)

    alleating = []
    allnoneating = []
    for i in range(len(eating)):
        alleating.extend(eating[i])
        
    for i in range(len(noneating)):
        allnoneating.extend(noneating[i])
        
    trials = 100
    for trial in range(trials):
        print 'Trial:', trial
        alleating_t = list(alleating)
        allnoneating_t = list(allnoneating)
        eatingtest = []
        noneatingtest = []
        for i in range(len(alleating)/10):
            j = random.randint(0, len(alleating_t)-1)
            eatingtest.append(alleating_t.pop(j))
            
        for i in range(len(allnoneating)/10):
            j = random.randint(0, len(allnoneating_t)-1)
            noneatingtest.append(allnoneating_t.pop(j))

        samples = alleating_t + allnoneating_t
        print len(samples)
        classes = [1 for i in range(len(alleating_t))] + [0 for i in range(len(allnoneating_t))]
        #print classes
        clf = DecisionTreeClassifier(random_state = 0)
        clf.fit(samples, classes)
        print len(alleating_t), len(allnoneating_t), len(eatingtest), len(noneatingtest)
        #print eatingtest
        correct = sum(clf.predict(eatingtest))
        incorrect = sum(clf.predict(noneatingtest))
        totalcorrect += correct
        totalpredicted += correct + incorrect
        total += float(len(eatingtest))
        #print clf.predict(noneatingtest)

print 'Precision:', totalcorrect/totalpredicted*100., 'Recall:', totalcorrect/total*100.
