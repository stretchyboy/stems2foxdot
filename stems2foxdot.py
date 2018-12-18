import os
import glob
from pydub import AudioSegment
from pydub import silence
import math
import json
import array
import numpy as np
import statistics

import argparse

parser = argparse.ArgumentParser(description='Create Samples From a Folder of Stems.')
parser.add_argument('path', metavar='PATH', type=str,
                    help='Path to stems folder')

parser.add_argument('-b','--bpm', type=int, nargs='?', default=110,
                    help='BPM of stems')

parser.add_argument('-g','--gaplength',  type=int, nargs='?', default=2,
                    help='Number of beats silence to detect as a gap between samples')

parser.add_argument('-r','--barlength', type=int, nargs='?', default=4,
                    help='Number of beats per bar')

parser.add_argument('-l','--limit', type=int, nargs='?', default=-32,
                    help='Decibel limit of silence')


args = parser.parse_args()


stem_dir = os.path.abspath(args.path) #'/home/meggleton/.local/lib/python3.6/site-packages/FoxDot/snd/_loop_/'  # Path where the videos are located

stem_name = os.path.basename(args.path)
#stem_dir = loop_dir + stem_name

os.chdir(stem_dir)

bpm = args.bpm
beat = 1000 * 60 / bpm
gaplength = args.gaplength
barlength = args.barlength
limit=args.limit
makesamples = True

cachefile = "cache"+str(limit)+"-"+str(gaplength)+".json"

samplesdata = {};

if (os.path.exists(cachefile)):
    f = open(cachefile, "r")
    content = f.read()
    f.close()
    samplesdata = json.loads(content)
else:
    for stemfile in glob.glob("*.wav"):
        print("Finding samples in "+stemfile)
        stem = AudioSegment.from_file(stemfile)
        sounds = silence.detect_nonsilent(stem, int(beat*gaplength), limit)
        samplesdata[stemfile] = sounds

    content = json.dumps(samplesdata, sort_keys=True,  indent=4, separators=(',', ': '))
    f = open(cachefile, "w")
    f.write(content)
    f.close()

foxdot = '''##################################################################################
# Created with stems2foxdot by stretch
# From '''+stem_name+'''
# ©  with Permission
###################################################################################
'''+"Samples.addPath(\""+stem_dir+"\")\nClock.bpm = "+str(bpm)+"\n\n"

s = 1
for stemfile in samplesdata:
    print("Processing "+stemfile)

    foldername = os.path.splitext(os.path.basename(stemfile))[0].replace(" ","_")
    instrument = "s"+str(s)
    print(foldername)
    if (makesamples):
        stem = AudioSegment.from_file(stemfile)

        if (os.path.isdir(foldername)):
            filelist = glob.glob(os.path.join(foldername, "*.wav"))
            for f in filelist:
                os.remove(f)
        else:
            os.mkdir(foldername)

    i = 0
    samples = []

    for sound in samplesdata[stemfile]:
        start_b = int(math.floor(1.0*sound[0]/beat))
        end_b = int(1 + math.ceil(1.0*sound[1]/beat))
        dur_b = end_b-start_b

        start_i = int(start_b*beat)
        end_i = int(end_b*beat)

        print(start_b, end_b, dur_b, start_i, end_i)

        if (makesamples):
            print("Making sample "+str(i+1)+"/"+str(len(samplesdata[stemfile])))
            filename = foldername + "/"+'{0:03d}_'.format(i)+foldername.lower() + ".wav"
            awesome = stem[start_i:end_i]
            pad = 0
            if(dur_b % barlength == 0):
                out = awesome
            else:
                pad = barlength - (dur_b % barlength)
                print(dur_b, pad)
                pad_silence = AudioSegment.silent(duration=(pad*beat), frame_rate =awesome.frame_rate)
                out = awesome.append(pad_silence)

            samparr = hash(tuple(out.get_array_of_samples()))
            shifted_samples = hash(tuple(np.right_shift(out.get_array_of_samples(), 1)))

            dup = False
            if(samparr in samples):
                dup = True
            else:
                if(samparr in samples):
                    dup = True


            if(dup):
                print("duplicate found")
            else :
                print(len(out))
                out.export(filename, format="wav")
                line = instrument+" >> loop('"+foldername+"', sample="+str(i)+", dur="+str(dur_b+pad)+") # "+str(dur_b) +" beats @ "+str(start_b)+"\n\n" #Bass
                foxdot += line
                i += 1
                samples.append(samparr)

                samples.append(shifted_samples)

    foxdot += ""+instrument+".stop()\n\n"

    s += 1

foxfilename = stem_name+".py"
print(foxfilename)
foxfile = open(foxfilename, "w")
foxfile.write(foxdot)
foxfile.close()

foxfilename = "../../"+stem_name+".py"
foxfile = open(foxfilename, "w")
foxfile.write(foxdot)
foxfile.close()
