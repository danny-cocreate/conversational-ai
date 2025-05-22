# First, install the Hume AI Python SDK:
# pip install hume-ai

import os
from hume import HumeClient

# Ensure you have your Hume API key set as an environment variable
# export HUME_API_KEY="your_api_key_here"
api_key = os.getenv("HUME_API_KEY")

if not api_key:
    print("Error: HUME_API_KEY environment variable not set.")
    print("Please set it using: export HUME_API_KEY=\"your_api_key_here\"")
else:
    try:
        from hume.tts import PostedUtterance, FormatMp3

        client = HumeClient(api_key=api_key)

        # Simple text string to synthesize
        text_to_synthesize = "Hello, this is a test of the Hume Octave TTS API."

        print(f"Synthesizing text: '{text_to_synthesize}'")

        # Send text to the API and get the response
        # This example uses the synchronous API call
        # For streaming, you would use client.tts.synthesize_json_streaming()
        result = client.tts.synthesize_json(
            utterances=[
                PostedUtterance(text=text_to_synthesize)
            ],
            format=FormatMp3()
        )

        # Process the result (e.g., save audio, play audio)
        # The result structure depends on the API version and parameters
        # You would typically get audio data in the response
        # For this basic example, we'll just print a success message and the result structure
        print("Successfully received response from Hume TTS API.")
        # print("Result structure:")
        print("Result structure:")
        print(result)
        print(f"Type of result: {type(result)}")
        

        # Handle the audio data from the 'result' object.
        # Using native macOS audio playback with afplay
        import base64
        import tempfile
        import subprocess

        try:
            audio_bytes = base64.b64decode(result.generations[0].audio)

            # Save to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                tmp_file.write(audio_bytes)
                temp_file_path = tmp_file.name

            print(f"Audio saved to temporary file: {temp_file_path}")

            # Play the audio file using macOS native afplay command
            print("Playing audio...")
            subprocess.run(['afplay', temp_file_path], check=True)
            print("Finished playing audio.")

            # Clean up the temporary file
            os.remove(temp_file_path)
            print(f"Temporary file removed: {temp_file_path}")

        except Exception as audio_e:
            print(f"An error occurred while processing or playing audio: {audio_e}")

    except Exception as e:
        print(f"An error occurred: {e}")

# To run this script:
# 1. Make sure you have Python installed.
# 2. Install the Hume AI SDK: pip install hume-ai
# 3. Set your API key: export HUME_API_KEY="your_api_key_here"
# 4. Run the script: python hume_tts_basic.py