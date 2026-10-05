import os
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from elevenlabs.client import ElevenLabs
from manim import logger

from manim_voiceover.helper import create_dotenv_file, remove_bookmarks
from manim_voiceover.services.base import SpeechService

load_dotenv(find_dotenv(usecwd=True))


def create_dotenv_elevenlabs():
    # logger.info(
    #     "Check out https://voiceover.manim.community/en/stable/services.html#elevenlabs"
    #     " to learn how to create an account and get your subscription key."
    # )
    try:
        os.environ["ELEVENLABS_API_KEY"]
    except KeyError:
        if not create_dotenv_file(["ELEVENLABS_API_KEY"]):
            raise
        logger.info("The .env file has been created. Please run Manim again.")
        sys.exit()


create_dotenv_elevenlabs()


class ElevenLabsService(SpeechService):
    """Speech service for ElevenLabs API."""

    def __init__(
        self,
        voice_id: str | None = None,
        model_id: str = "eleven_multilingual_v2",
        output_format="mp3_44100_192",
        **kwargs,
    ):
        """
        Args:
            voice_id (str, Optional): The id of the voice to use.
                See the
                `API page <https://elevenlabs.io/docs/api-reference/text-to-speech>`
                for reference. Defaults to `None`. If none of `voice_name`
                or `voice_id` must be provided, it uses default available voice.
            model (str, optional): The name of the model to use. See the `API
                page: <https://elevenlabs.io/docs/api-reference/text-to-speech>`
                for reference. Defaults to `eleven_monolingual_v1`
            output_format (Union[OutputFormat, str], optional): The voice output
                format to use. Options are available depending on the Elevenlabs
                subscription. See the `API page:
                <https://elevenlabs.io/docs/api-reference/text-to-speech>`
                for reference. Defaults to `mp3_44100_128`.
        """

        self.voice = voice_id
        self.model = model_id
        self.output_format = output_format

        SpeechService.__init__(self, transcription_model=None, **kwargs)

    def generate_from_text(
        self,
        text: str,
        cache_dir: str | None = None,
        path: str | None = None,
        **kwargs,
    ) -> dict:
        if cache_dir is None:
            cache_dir: str | Path = self.cache_dir

        elevenlabs = ElevenLabs(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
        )

        clean_text = remove_bookmarks(text)

        input_data = {
            "input_text": clean_text,
            "service": "elevenlabs",
            "config": {
                "model": self.model,
                "voice": self.voice,
            },
        }

        # if not config.disable_caching:
        cached_result = self.get_cached_result(input_data, cache_dir)

        if cached_result is not None:
            return cached_result

        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".mp3"
        else:
            audio_path = path

        try:
            audio = elevenlabs.text_to_speech.convert(
                text=clean_text,
                voice_id=self.voice,
                model_id=self.model,
                output_format=self.output_format,
            )
        except Exception as e:
            logger.error(e)
            raise

        audio_path = path or self.get_audio_basename(input_data) + ".mp3"
        full_path = Path(cache_dir) / audio_path

        # Path(cache_dir).joinpath(full_path).write_bytes(
        #     base64.b64decode(response.audio)
        # )
        with open(str(full_path), "wb") as f:
            for chunk in audio:
                f.write(chunk)

        json_dict = {
            "clean_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }

        return json_dict
