import sys

from pydantic import ValidationError

from .schemas import Segment, Word
from ._core import stt_to_vtt as _convert

__version__ = "0.1.0"
__author__ = "Gary Lab"
__all__ = ["Word", "Segment", "ValidationError"]


# Single public API: stt2vtt(...). stt_to_vtt is not exposed.
_mod = sys.modules[__name__]
_mod.__class__ = type(
    _mod.__class__.__name__,
    (_mod.__class__,),
    {"__call__": lambda self, *args, **kwargs: _convert(*args, **kwargs)},
)
