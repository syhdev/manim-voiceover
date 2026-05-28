from manim import *
from manim_voiceover.services.mistralai import MistralAIService
from manim_voiceover import VoiceoverScene


class MistralAIExample(VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            MistralAIService(
                voice="a1b08953-06dd-4848-b71c-3267dcfedad2",
                model="voxtral-mini-tts-2603",
            )
        )

        circle = Circle()

        with self.voiceover(text="This circle is drawn as I speak.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)

        self.wait()