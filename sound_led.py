# Sound_level - this program reads the output volume level and stores it as a variable rms
# We then check the value of rms and if greater than a specific value (we have sound) we turn on an LED
# Needs to be tested on a Pi

from gpiozero import LED
import pyaudio
import audioop
from time import sleep

# Initialize the GPIO pins
led = LED(17)
# Turn off LED
led.off()

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 60

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)


for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK, exception_on_overflow=False)
    rms = audioop.rms(data, 2)   
    print(rms)
    if rms > 200:
        print("Sound Detected")
        led.on()
        sleep(0.025) 
        led.off()
        
led.off()
stream.stop_stream()
stream.close()
p.terminate()


