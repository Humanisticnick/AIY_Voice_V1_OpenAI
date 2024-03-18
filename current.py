import threading
import time
import pyaudio
import wave
from openai import OpenAI
from pathlib import Path
import datetime
import RPi.GPIO as GPIO
import traceback
import os
import sys


# GPIO pin configuration
BUTTON_PIN = 23  # Example GPIO pin for button
LED_PIN = 25  # Example GPIO pin for LED

# Setup GPIO
GPIO.setmode(GPIO.BCM)  # Use Broadcom pin-numbering scheme
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button pin set as input
GPIO.setup(LED_PIN, GPIO.OUT)  # LED pin set as output

# Get today's date in the format XX/XX/XXXX
today_date = datetime.datetime.now().strftime("%m/%d/%Y")


# Error sound if something goes wrong
def play_error_sound():
    try:
        print("Playing Error Sound")
        wf = wave.open('error.wav', 'rb')
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)
        data = wf.readframes(256)
        while len(data) > 0:
            stream.write(data)
            data = wf.readframes(256)
        stream.stop_stream()
        stream.close()
        p.terminate()
    except Exception as e:
        print("Failed to play error sound:", e)

# Define the blinking behavior
def blink_led():
    while is_processing:
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(0.5)  # On for 0.5 seconds
        GPIO.output(LED_PIN, GPIO.LOW)
        time.sleep(0.5)  # Off for 0.5 seconds

# Setup GPIO
GPIO.setmode(GPIO.BCM)  # Use Broadcom pin-numbering scheme
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button pin set as input
GPIO.setup(LED_PIN, GPIO.OUT)  # LED pin set as output

# Audio recording parameters
capture_device_index = 0
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 128
WAVE_OUTPUT_FILENAME = "file.wav"

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Recording flag and frames buffer
is_recording = False
frames = []

# OpenAI API key
api_key = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'  # Replace with your actual API key
client = OpenAI(api_key=api_key)

# Define the system message
initial_system_message = {
    "role": "system",
    "content": "You are a voice assistant. Your objective is to answer questions accrautely and to be enjoyable to talk to."
}

# Global variable to hold conversation state
conversation_history = [initial_system_message]

# Function to record audio
def record_audio():
    print("Recording audio")
    global is_recording, frames
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []
    while is_recording:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
    stream.stop_stream()
    stream.close()

# Function to transcribe audio
def transcribe_audio(file_path):
    print("Turning audio to text..")
    try:
        with open(file_path, "rb") as audio_file:
            transcription_response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en",
                response_format="text"
            )
        print("Text Heard:", transcription_response)  # Debugging line
        return transcription_response
    except Exception as e:
        print(f"Error in audio transcription: {e}")
        exit()

# Inactivity timer for clearing conversation history
inactivity_timer = None
inactivity_limit = 600  # 10 minutes, 600 seconds

def reset_inactivity_timer():
    global inactivity_timer, conversation_history
    if inactivity_timer is not None:
        inactivity_timer.cancel()

    def clear_history():
        global conversation_history
        print("Clearing conversation history due to inactivity.")
        conversation_history = [initial_system_message]

    inactivity_timer = threading.Timer(inactivity_limit, clear_history)
    inactivity_timer.start()

def get_chat_response(prompt):
    global conversation_history
    reset_inactivity_timer()  # Reset the inactivity timer each time a new prompt is processed

    conversation_history.append({"role": "user", "content": prompt})
    print("Getting answer from AI")
    chat_response = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=conversation_history,
        temperature=0.9,
        max_tokens=512,
        top_p=0.9,
        frequency_penalty=0.2,
        presence_penalty=0
    )

    response_content = chat_response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": response_content})
    print(response_content)
    return response_content

# Function to convert text to speech
def text_to_speech(text):
    print("Converting Response to Audio")
    audio_response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
        response_format="wav"
    )
    return audio_response.content

# Function to play WAV file
def play_wav(file_content):
    print("Playing Audio Response")
    speech_file_path = Path("response.wav")
    with open(speech_file_path, 'wb') as file:
        file.write(file_content)
    wf = wave.open(str(speech_file_path), 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    data = wf.readframes(256)
    while len(data) > 0:
        stream.write(data)
        data = wf.readframes(256)
    stream.stop_stream()
    stream.close()
    p.terminate()

# Main Function
def main():
    while True:  # Loop to allow restarting the process
        try:
            print('Press and hold the button to record audio.')
            GPIO.output(LED_PIN, GPIO.LOW)
            while True:
                GPIO.wait_for_edge(BUTTON_PIN, GPIO.FALLING)
                global is_recording
                is_recording = True
                GPIO.output(LED_PIN, GPIO.HIGH)  # Solid on while recording

                record_thread = threading.Thread(target=record_audio)
                record_thread.start()

                GPIO.wait_for_edge(BUTTON_PIN, GPIO.RISING)
                is_recording = False
                record_thread.join()

                GPIO.output(LED_PIN, GPIO.LOW)  # Turn off LED before processing

                global is_processing
                is_processing = True
                blink_thread = threading.Thread(target=blink_led)
                blink_thread.start()

                waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
                waveFile.setnchannels(CHANNELS)
                waveFile.setsampwidth(audio.get_sample_size(FORMAT))
                waveFile.setframerate(RATE)
                waveFile.writeframes(b''.join(frames))
                waveFile.close()

                transcript = transcribe_audio(WAVE_OUTPUT_FILENAME)
                response_text = get_chat_response(transcript)
                speech_content = text_to_speech(response_text)
                play_wav(speech_content)

                is_processing = False
                blink_thread.join()

                GPIO.output(LED_PIN, GPIO.LOW)  # Solid on when ready for the next input
                print("Ready for next audio")

        except KeyboardInterrupt:
            print("Exiting program")
            break  # Exit the loop and terminate the program
        except Exception as e:
            print("An error occurred:", e)
            traceback.print_exc()
            #Play Error Sound
            play_error_sound()
            print("Attempting to restart process...")
            #Restart the script from the begining
            os.execl(sys.executable, sys.executable, *sys.argv)

        finally:
            GPIO.cleanup()  # Clean up GPIO on normal exit or error recovery

if __name__ == '__main__':
    main()

    #kill the script pkill -f current_adult.py
