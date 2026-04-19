from __future__ import annotations

from io import BytesIO
from typing import Optional

from gtts import gTTS


def synthesize_briefing(text: str, lang: str = "en") -> Optional[bytes]:
    try:
        buffer = BytesIO()
        tts = gTTS(text=text, lang=lang)
        tts.write_to_fp(buffer)
        return buffer.getvalue()
    except Exception:
        return None
