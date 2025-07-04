import os
from elevenlabs import generate, set_api_key
from typing import Union, Iterator

# Get API key from environment variable
api_key = os.getenv("ELEVEN_API_KEY")
if not api_key:
    raise ValueError("ELEVEN_API_KEY environment variable is not set")

# Set the API key
set_api_key(api_key)

# Try to generate audio
try:
    audio = generate(
        text="This is a test of the ElevenLabs text to speech system.",
        voice="Rachel",
        model="eleven_monolingual_v1"
    )
    
    # Save the audio to a file
    with open("test_output.mp3", "wb") as f:
        if isinstance(audio, bytes):
            f.write(audio)
        else:
            for chunk in audio:
                f.write(chunk)
    print("Successfully generated audio! Check test_output.mp3")
    
except Exception as e:
    print(f"Error generating audio: {e}") 