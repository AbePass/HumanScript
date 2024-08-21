import os
import time
import logging
import tempfile
import numpy as np
import pygame
import openai
import speech_recognition as sr
from Settings.config import *

class AudioManager:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.wake_word = WAKE_WORD
        self.is_listening = False
        pygame.mixer.init()

    def generate_beep(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2)
        t = np.linspace(0, BEEP_DURATION, int(44100 * BEEP_DURATION), False)
        beep = np.sin(2 * np.pi * BEEP_FREQUENCY * t)
        beep = (beep * 32767).astype(np.int16)
        stereo_beep = np.column_stack((beep, beep))  # Create stereo audio
        sound = pygame.sndarray.make_sound(stereo_beep)
        sound.play()

    def recognize_speech(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        
        recognizer = sr.Recognizer()
        logging.info("Listening for command...")
        
        try:
            with sr.Microphone() as source:
                logging.info("Adjusting for ambient noise...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                logging.info("Listening...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            logging.info("Audio captured, attempting to transcribe...")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                temp_audio.write(audio.get_wav_data())
                temp_audio_path = temp_audio.name
            
            with open(temp_audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            
            user_input = transcript.text
            logging.info(f"Transcribed: {user_input}")
            return user_input
        
        except sr.WaitTimeoutError:
            logging.warning("Listening timed out. No speech detected.")
            return "Listening timed out. Please try again."
        except Exception as e:
            logging.error(f"Error in speech recognition: {str(e)}")
            return f"Error in speech recognition: {str(e)}"
        finally:
            if 'temp_audio_path' in locals():
                try:
                    os.unlink(temp_audio_path)
                    logging.info(f"Temporary audio file deleted: {temp_audio_path}")
                except FileNotFoundError:
                    logging.warning(f"Could not delete temporary file: {temp_audio_path}")

    def text_to_speech(self, text):
        pygame.mixer.init()
        response = self.client.audio.speech.create(
            model=TTS_SETTINGS["model"],
            voice=TTS_SETTINGS["voice"],
            input=text
        )
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(response.content)
            temp_audio_path = temp_audio.name
        
        pygame.mixer.music.load(temp_audio_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            if not self.is_listening:  # Add this line to check if playback should be stopped
                break
        
        pygame.mixer.music.unload()
        time.sleep(0.1)
        
        try:
            os.unlink(temp_audio_path)
        except FileNotFoundError:
            logging.warning(f"Could not delete temporary file: {temp_audio_path}")

    def stop_playback(self):
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            logging.info("Audio playback interrupted")

    def listen_for_wake_word(self, wake_word):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                logging.info("Listening for wake word...")
                audio = recognizer.listen(source, phrase_time_limit=3)
            text = recognizer.recognize_google(audio).lower()
            logging.info(f"Heard: {text}")
            return wake_word in text
        except sr.UnknownValueError:
            return False
        except Exception as e:
            logging.error(f"Error listening for wake word: {str(e)}")
            return False