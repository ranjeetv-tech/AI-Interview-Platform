from abc import ABC, abstractmethod

class SpeechToTextProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes) -> str: ...

class TextToSpeechProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> bytes: ...

class BrowserSpeechProvider:
    """Marker abstraction: STT/TTS are implemented in the browser with Web Speech APIs.
    Keeping this interface lets a cloud/local provider be added later without changing interview logic.
    """
    name = "browser"
