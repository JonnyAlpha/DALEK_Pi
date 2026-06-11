# DALEK_Pi
A repository created to store items related to my DALEK Pi project.

**daleh.sh** - is a bash script that, when run, takes live audio from the microphone and adds various effects to simulate a Dalek voice.

**dalekout.wav** - is a recording to demonstrate the results.

**sound_level.py** is a Python program that reads the sound output and displays it as an integer.

**sound_led.py** is an extension of sound_level.py that takes the integer output and uses it to control an led to create sound to light for the Dalek Dome lights.

**dalek_pyaudio.py** is a complete rewrite to add live audio effects in python, it also contains the code to iluminate the dalek Dome Lights (12vLEDs) based on rms level of the csound. The circuit works by switching on an N Channel MOSFET when the audi level exceeds a specific level. 
