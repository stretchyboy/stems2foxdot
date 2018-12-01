import os
import glob
from pydub import AudioSegment
from pydub import silence
import math
import json

loop_dir = '/home/meggleton/.local/lib/python2.7/site-packages/FoxDot/snd/_loop_/'  # Path where the videos are located

stem_name = "Bullet"
stem_dir = loop_dir + stem_name

os.chdir(stem_dir)

bpm = 110
beat = 1000 * 60 / bpm
gaplength = 2
barlength = 4
limit=-32
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

foxdot = "Clock.bpm = "+str(bpm)+"\n\n"

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

    i = 1
    for sound in samplesdata[stemfile]:
        #print(sound[0], 1.0*sound[0]/beat,sound[1], 1.0*sound[1]/beat)
        start_b = int(math.floor(1.0*sound[0]/beat))
        end_b = int(math.ceil(1.0*sound[1]/beat))
        dur_b = end_b-start_b

        start_i = int(math.floor(1.0*sound[0]/beat)*beat)
        end_i = int(math.ceil(1.0*sound[1]/beat)*beat)


        if (makesamples):
            print("Making sample "+str(i)+"/"+str(len(samplesdata[stemfile])))
            filename = foldername + "/"+foldername.lower()+'_{0:03d}'.format(i) + ".wav"
            awesome = stem[start_i:end_i]
            pad = 0
            if(dur_b % barlength == 0):
                out = awesome
            else:
                pad = barlength - (dur_b % barlength)
                print(dur_b, pad)
                pad_silence = AudioSegment.silent(duration=(pad*beat), frame_rate =awesome.frame_rate)
                out = awesome.append(pad_silence)


            out.export(filename, format="wav")

            line = instrument+" >> loop('"+stem_name+"/"+foldername+"', sample="+str(i)+", dur="+str(dur_b+pad)+") # "+str(dur_b) +" beats @ "+str(start_b)+"\n\n" #Bass
            foxdot += line


        i += 1
    s += 1

foxfile = open("foxdot.py", "w")
foxfile.write(foxdot)
foxfile.close()
