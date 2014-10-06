import pyaudio
import wave
import audioop
from collections import deque
import os
import urllib2
import urllib
import time
import math
import json

LANG_CODE = 'en-US'  # Language to use

#add your API KEY here in the link
GOOGLE_SPEECH_URL = 'https://www.google.com/speech-api/v2/recognize?output=json&lang=en-us&key=API_KEY_ADD_HERE'

FLAC_CONV = 'flac -f'  # We need a WAV to FLAC converter. flac is available on Linux or can
			#be downloaded using sudo apt-get install flac

# Microphone stream config.
CHUNK = 1024  # CHUNKS of bytes to read each time from mic
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"
THRESHOLD = 2500  # The threshold intensity that defines silence
                  # and noise signal (an int. lower than THRESHOLD is silence).

SILENCE_LIMIT = 1  # Silence limit in seconds. The max ammount of seconds where
                   # only silence is recorded. When this time passes the
                   # recording finishes and the file is delivered.

PREV_AUDIO = 0.5  # Previous audio (in seconds) to prepend. When noise
                  # is detected, how much of previously recorded audio is
                  # prepended. This helps to prevent chopping the beggining
                  # of the phrase.

def listen_for_speech(threshold=THRESHOLD):
    """
    Listens to Microphone, extracts phrases from it and sends it to
    Google's TTS service and returns response. a "phrase" is sound
    surrounded by silence (according to threshold). num_phrases controls
    how many phrases to process before finishing the listening process
    (-1 for infinite).
    """

    #Open stream
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

    print("* recording")

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
	data = stream.read(CHUNK)
        frames.append(data)

    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    response = stt_google_wav(WAVE_OUTPUT_FILENAME)

    return response

def stt_google_wav(audio_fname):
    """ Sends audio file (audio_fname) to Google's text to speech
        service and returns service's response. We need a FLAC
        converter if audio is not FLAC (check FLAC_CONV). """

    print "Sending ", audio_fname
    #Convert to flac first
    filename = audio_fname
    del_flac = False
    if 'flac' not in filename:
        del_flac = True
        print "Converting to flac"
        print FLAC_CONV + filename
        os.system(FLAC_CONV + ' ' + filename)
        filename = filename.split('.')[0] + '.flac'

    f = open(filename, 'rb')
    flac_cont = f.read()
    f.close()
    
    req = urllib2.Request(GOOGLE_SPEECH_URL, data=flac_cont, headers={'Content-type': 'audio/x-flac; rate=44100;'})

    try:
	ret = urllib2.urlopen(req)
    except urllib2.URLError:
        print "Error Transcribing Voicemail"
        sys.exit(1)

    responses=[]
    responses = ret.read()
    #print responses
    text = json.loads(json.dumps(responses))

    if del_flac:
        os.remove(filename)  # Remove temp file

    return text


if(__name__ == '__main__'):
    print listen_for_speech()  # listen to mic.
    #print stt_google_wav('good-morning-google.flac')  # translate audio file
