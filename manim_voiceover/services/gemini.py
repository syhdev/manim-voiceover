import os
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from google.cloud import texttospeech
from manim import logger

from manim_voiceover.helper import (
    create_dotenv_file,
    remove_bookmarks,
)
from manim_voiceover.services.base import SpeechService

load_dotenv(find_dotenv(usecwd=True))


def create_dotenv_gemini():
    logger.info(
        "You need a Gemini API key from https://makersuite.google.com/app/apikey"
    )
    if not create_dotenv_file(["GOOGLE_API_KEY"]):
        raise ValueError(
            "The environment variable GOOGLE_API_KEY is not set. "
            "Please add it to your .env file."
        )
    logger.info("The .env file has been created. Please restart Manim.")
    sys.exit()


class GeminiTTSService(SpeechService):
    """
    Gemini-based TTS service using Google's Gemini 2.5 SDK.
    See https://cloud.google.com/text-to-speech/docs/voices for all voices.
    """

    def __init__(
        self,
        voice_id: str | None = None,
        model_id: str = "gemini-3.1-flash-tts-preview",
        **kwargs,
    ):
        self.model_id = model_id
        self.voice_id = voice_id

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            # create_dotenv_gemini()
            pass

        self.client = texttospeech.TextToSpeechClient()

        super().__init__(transcription_model=None, **kwargs)

    def generate_from_text(
        self, text: str, cache_dir: str | None = None, path: str | None = None, **kwargs
    ) -> dict:
        if cache_dir is None:
            cache_dir: str | Path = self.cache_dir

        clean_text = remove_bookmarks(text)

        input_data = {
            "input_text": clean_text,
            "service": "gemini",
            "config": {
                "model": self.model_id,
                "voice": self.voice_id,
            },
        }

        cached = self.get_cached_result(input_data, cache_dir)
        if cached:
            return cached

        try:
            # Set the text input to be synthesized
            synthesis_input = texttospeech.SynthesisInput(text=clean_text)

            # Build the voice request, select the language code ("fr-FR") and the ssml
            # voice gender ("neutral")
            voice = texttospeech.VoiceSelectionParams(
                language_code="fr-FR",
                name=self.voice_id,
            )

            # Select the type of audio file you want returned
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=44100,
            )
            response = self.client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

        except Exception as e:
            logger.error(f"Gemini TTS generation failed: {e}")
            raise

        audio_data = response.audio_content

        audio_path = path or self.get_audio_basename(input_data) + ".wav"
        full_path = Path(cache_dir) / audio_path

        # Save audio
        # with wave.open(str(full_path), "wb") as wf:
        #     wf.setnchannels(1)
        #     wf.setsampwidth(2)
        #     wf.setframerate(44100)
        #     wf.writeframes(audio_data)

        with open(str(full_path), "wb") as f:
            f.write(audio_data)

        return {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }
