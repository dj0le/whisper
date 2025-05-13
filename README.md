# Real-time Speech-to-Text with Whisper

This script performs real-time speech-to-text transcription using the Whisper model. It captures audio from your default microphone, processes it, and displays the transcribed text. No API key is required.

## Features

*   Real-time transcription: Transcribes audio as it's being recorded.
*   Uses the Whisper model: Employs OpenAI's Whisper model for accurate speech recognition.
*   Noise detection: Includes a silence threshold to avoid transcribing silence.
*   Resampling: Resamples audio to the appropriate sample rate for Whisper.
*   Cross-platform: Works on any platform supported by `sounddevice` and Whisper.

## Requirements

Before running the script, ensure you have the following installed:

*   Python 3.7+
*   [Whisper](https://github.com/openai/whisper): `pip install -U whisper-ai`
*   [Sounddevice](https://python-sounddevice.readthedocs.io/): `pip install sounddevice`
*   [NumPy](https://numpy.org/): `pip install numpy`

You also need to have a working audio input device (microphone).

## Installation

1.  Clone the repository (or download the script `mic-record.py`):

    ```/dev/null/bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  Install the required Python packages:

    ```/dev/null/bash
    pip install -r requirements.txt
    ```

## Usage

1.  Run the script:

    ```/dev/null/bash
    python whisper/mic-record.py
    ```

2.  The script will list available audio devices and start listening on your default input device.

3.  Speak into your microphone. The transcribed text will be displayed in the console.

4.  Press `Ctrl+C` to stop the transcription.

## Configuration

The following parameters can be adjusted in the script:

*   `BUFFER_SIZE`: Size of the audio buffer (default: 1024).
*   `AUDIO_BUFFER_DURATION`: Duration of audio to buffer before processing (default: 1.0 second).
*   `INPUT_SAMPLE_RATE`: Input sample rate from the audio device (default: 48000 Hz).
*   `WHISPER_SAMPLE_RATE`: Sample rate required for Whisper (default: 16000 Hz).
*   `SILENCE_THRESHOLD`: Threshold for detecting silence (default: 0.01).
*   `model = whisper.load_model("base")`:  You can change the whisper model size here.  Available options are `tiny`, `base`, `small`, `medium`, or `large`.


## Notes

*   The script uses the default audio input device. You can modify the script to select a specific device if needed.
*   The `base` Whisper model is used by default.  You can change this in the script if desired, but it will affect performance and accuracy.
*   This script is intended for real-time transcription and may not be suitable for transcribing long audio files.
