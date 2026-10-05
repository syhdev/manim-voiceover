# import pkg_resources
import importlib.metadata

from syh_manim_voiceover.tracker import VoiceoverTracker as VoiceoverTracker
from syh_manim_voiceover.voiceover_scene import VoiceoverScene as VoiceoverScene

# __version__: str = pkg_resources.get_distribution(__name__).version

__version__: str = importlib.metadata.version(__name__)
