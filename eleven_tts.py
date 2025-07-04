import os
from typing import AsyncGenerator
from elevenlabs import generate, set_api_key
from livekit.plugins.base import TTS, TTSResult, TTSResultChunk, TTSMetadata, TTSCapabilities


class ElevenLabsTTS(TTS):
    def __init__(self, voice_id: str = None):
        self.api_key = os.getenv("ELEVEN_API_KEY")
        self.voice_id = voice_id or os.getenv("ELEVEN_VOICE_ID") or "Rachel"

        if not self.api_key:
            raise ValueError("ELEVEN_API_KEY environment variable is not set")

        set_api_key(self.api_key)

    @property
    def capabilities(self) -> TTSCapabilities:
        return TTSCapabilities(
            streaming=False,
            multi_utterance=False
        )

    async def synthesize(self, text: str) -> TTSResult:
        audio = generate(
            text=text,
            voice=self.voice_id,
            model="eleven_monolingual_v1"
        )
        return TTSResult(audio=audio, metadata=TTSMetadata())

    async def stream(self, text: str) -> AsyncGenerator[TTSResultChunk, None]:
        raise NotImplementedError("Streaming not implemented yet.")
