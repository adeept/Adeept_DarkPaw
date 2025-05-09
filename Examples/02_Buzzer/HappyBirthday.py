#!/usr/bin/env/python3
# File name   : HappyBirthday.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/23
from gpiozero import TonalBuzzer
from time import sleep

# Initialize a TonalBuzzer connected to GPIO18 (BCM)
tb = TonalBuzzer(18)


# Define the "Happy Birthday" song
HAPPY_BIRTHDAY_SONG = [
    ["G4", 0.3], ["G4", 0.3], ["A4", 0.3], ["G4", 0.3], ["C5", 0.3], ["B4", 0.6],
    ["G4", 0.3], ["G4", 0.3], ["A4", 0.3], ["G4", 0.3], ["D5", 0.3], ["C5", 0.6],
    ["G4", 0.3], ["G4", 0.3], ["C5", 0.3], ["B4", 0.3], ["C5", 0.3], ["B4", 0.3], ["A4", 0.6],
    ["F5", 0.3], ["F5", 0.3], ["B4", 0.3], ["C5", 0.3], ["D5", 0.3], ["C5", 0.6]
]

def play(tune):
    """
    Play a musical tune using the buzzer.
    :param tune: List of tuples (note, duration), 
    where each tuple represents a note and its duration.
    """
    for note, duration in tune:
        print(note)  # Output the current note being played
        tb.play(note)  # Play the note on the buzzer
        sleep(float(duration))  # Delay for the duration of the note
    tb.stop()  # Stop playing after the tune is complete

if __name__ == "__main__":
    try:
        # Third demo: Play the entire "Happy Birthday" song
        print("Demo: Playing the Happy Birthday song")
        play(HAPPY_BIRTHDAY_SONG)

    except KeyboardInterrupt:
        # Handle KeyboardInterrupt for graceful termination
        tb.stop()
        print("Program terminated by user.")
