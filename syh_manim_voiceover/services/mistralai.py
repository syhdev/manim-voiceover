import base64
import os
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from manim import logger
from mistralai.client import Mistral

from manim_voiceover.helper import (
    create_dotenv_file,
    prompt_ask_missing_extras,
    remove_bookmarks,
)
from manim_voiceover.services.base import SpeechService

load_dotenv(find_dotenv(usecwd=True))


def create_dotenv_mistralai():
    logger.info(
        "Check out https://docs.mistral.ai/studio-api/audio/text_to_speech to learn how to create an account and get your API key."
    )
    if not create_dotenv_file(["MISTRAL_API_KEY"]):
        raise ValueError(
            "The environment variable MISTRAL_API_KEY is not set. Please set it "
            "or create a .env file with the variables."
        )
    logger.info("The .env file has been created. Please run Manim again.")
    sys.exit()


class MistralAIService(SpeechService):
    """
    Speech service class for Mistral AI TTS Service. See the `Mistral AI API page
    <https://docs.mistral.ai/studio-api/audio/text_to_speech>`__
    for more information about voices and models.
    """

    def __init__(
        self,
        voice_id: str | None = None,
        model_id: str = "voxtral-mini-tts-2603",
        **kwargs,
    ):
        """
        Args:
            voice_id (str, optional): The voice to use. See the
                `API page <https://docs.mistral.ai/studio-api/audio/text_to_speech>`__
                for all the available options. Defaults to ``"default"``.
            model (str, optional): The TTS model to use.
                See the `API page <https://docs.mistral.ai/studio-api/audio/text_to_speech>`__
                for all the available options. Defaults to ``"voxtral-tts-26-03"``.
            transcription_model (str, optional): The Whisper model to use for transcription.
                Defaults to None.
        """

        prompt_ask_missing_extras("mistralai", "mistralai", "MistralAIService")
        self.voice_id = voice_id
        self.model_id = model_id

        SpeechService.__init__(self, transcription_model=None, **kwargs)

    def generate_from_text(
        self, text: str, cache_dir: str | None = None, path: str | None = None, **kwargs
    ) -> dict:
        """"""

        if cache_dir is None:
            cache_dir: str | Path = self.cache_dir

        input_text = remove_bookmarks(text)

        input_data = {
            "input_text": input_text,
            "service": "mistralai",
            "config": {
                "voice": self.voice_id,
                "model": self.model_id,
            },
        }

        cached_result = self.get_cached_result(input_data, cache_dir)
        if cached_result is not None:
            print(
                "Cache hit for text:",
                text,
                "with voice:",
                self.voice_id,
                "and model:",
                self.model_id,
            )
            return cached_result

        print(
            "Cache miss for text:",
            text,
            "with voice:",
            self.voice_id,
            "and model:",
            self.model_id,
        )

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path

        if os.getenv("MISTRAL_API_KEY") is None:
            # create_dotenv_mistralai()
            pass

        # Initialize Mistral client
        client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

        print(
            f"Generating speech for text: {input_text} with voice: {self.voice_id} and model: {self.model_id}"
        )

        try:
            # Use the Mistral SDK to generate speech
            response = client.audio.speech.complete(
                model=self.model_id,
                input=input_text,
                voice_id=self.voice_id,
                response_format="mp3",
            )

            # Save the audio file
            # with open(str(Path(cache_dir) / audio_path), "wb") as f:
            #     f.write(response)
            # print(audio_path)
            Path(cache_dir).joinpath(audio_path).write_bytes(
                base64.b64decode(response.audio_data)
            )
            # tts.save(str(Path(cache_dir) / audio_path))

        except Exception as e:
            logger.error(f"Mistral AI TTS SDK request failed: {e}")
            raise

        json_dict = {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict
