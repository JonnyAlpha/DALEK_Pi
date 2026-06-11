mport numpy as np
import pyaudio
import wave
import sys
import math
from gpiozero import LED
from time import sleep

# NOTE TEST_MODE does additional import

# --- CONFIGURATION ---
LED_THRESHOLD = 200  
MOD_FREQUENCY = 30.0
RATE = 20050 # Sample rate - Half normal sample rate fine for distorted sound
CHUNK = 1024
DISTORTION_DRIVE = 5.0   # tanh pre-gain, increase for more distortion
LOWPASS_CUTOFF = 3000    # Hz

# usage:
# python dalek.py : live use
# python dalek.py source.wav : process wav file to audio device
# python dalek.py source.wav out.wav : process wav file to output wav file

# Setup Hardware

led=LED(18)

# Test mode args
TEST_MODE = len(sys.argv) > 1
TEST_FILE = sys.argv[1] if TEST_MODE else None
TEST_OUT_FILE = sys.argv[2] if len(sys.argv) > 2 else None

phase = 0.0

# Simple one-pole lowpass filter state
# see https://www.dspguide.com/ch19/2.htm
lp_state = 0.0
lp_alpha = 1.0 - math.exp(-2.0 * math.pi * LOWPASS_CUTOFF / RATE)

def lowpass(audio):
    global lp_state
    out = np.zeros_like(audio)
    for i in range(len(audio)):
        lp_state += lp_alpha * (audio[i] - lp_state)
        out[i] = lp_state
    return out

def process_chunk(audio_int16):
    global phase

    rms = int(np.sqrt(np.mean(audio_int16.astype(np.float32)**2)))
    # LED Addition
    led.on() if rms > LED_THRESHOLD else led.off()

    audio_float = audio_int16.astype(np.float32) / 32768.0

    # Tanh distortion
    audio_float = np.tanh(audio_float * DISTORTION_DRIVE) / math.tanh(DISTORTION_DRIVE)

    # Ring modulation
    t = (np.arange(len(audio_float)) + phase) / RATE
    carrier = np.sin(2 * np.pi * MOD_FREQUENCY * t)
    audio_float = audio_float * carrier
    phase = math.fmod(phase + len(audio_float), RATE)

    # Lowpass filter
    audio_float = lowpass(audio_float)

    processed = np.clip(audio_float * 32768.0, -32768, 32767).astype(np.int16)

    scale = 1/250
    max_line_length = 100
    bar = ('*' * int(rms * scale))[:max_line_length - 13]
    print(f"RMS: {rms:5d} | {bar}".ljust(max_line_length), end='\r')

    return processed

def audio_callback(in_data, frame_count, time_info, status):
    audio_int16 = np.frombuffer(in_data, dtype=np.int16)
    processed = process_chunk(audio_int16)
    return (processed.tobytes(), pyaudio.paContinue)

p = pyaudio.PyAudio()

if TEST_MODE:
    import scipy.signal as signal

    wf = wave.open(TEST_FILE, 'rb')

    if TEST_OUT_FILE:
        wfout = wave.open(TEST_OUT_FILE, 'wb')
        wfout.setnchannels(1)
        wfout.setsampwidth(2)
        wfout.setframerate(RATE)

    file_rate = wf.getframerate()
    file_channels = wf.getnchannels()

    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    output=True,
                    frames_per_buffer=CHUNK)

    print(f"Test mode: {TEST_FILE} ({file_rate}Hz, {file_channels}ch)")
    print("Press Ctrl+C to stop.\n")
    try:
        while True:
            raw = wf.readframes(CHUNK)
            if not raw:
                break
            audio_int16 = np.frombuffer(raw, dtype=np.int16)

            if file_channels == 2:
                audio_int16 = audio_int16.reshape(-1, 2).mean(axis=1).astype(np.int16)

            if file_rate != RATE:
                n_samples = int(len(audio_int16) * RATE / file_rate)
                audio_int16 = signal.resample(audio_int16, n_samples)
                #raw_bytes = audio_int16.tobytes()

                #resampled, _ = audioop.ratecv(raw_bytes, 2, 1, file_rate, RATE, None)
                #audio_int16 = np.frombuffer(resampled, dtype=np.int16)

            processed = process_chunk(audio_int16)

            if TEST_OUT_FILE:
                wfout.writeframes(processed.tobytes())
            else:
                stream.write(processed.tobytes())

    except KeyboardInterrupt:
        print("\n\nStopping...")

    wf.close()
    if TEST_OUT_FILE:
        wfout.close()
        print("Written ", TEST_OUT_FILE)

else:
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    input=True,
                    output=True,
                    frames_per_buffer=CHUNK,
                    stream_callback=audio_callback)

    print("FX Chain: RingMod -> Distortion -> Lowpass")
    print("Press Ctrl+C to stop.\n")

    try:
        while stream.is_active():
            sleep(0.1)
    except KeyboardInterrupt:
        print("\n\nStopping...")

stream.stop_stream()
stream.close()
p.terminate()
