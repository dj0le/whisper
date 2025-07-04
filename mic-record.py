import sounddevice as sd
import numpy as np
import whisper
import queue
import threading
import time
import signal
import sys
import atexit
import pyperclip

# Load the Whisper model
model = whisper.load_model("small") # choose from small, base, medium, large-v3

# Audio parameters
BUFFER_SIZE = 1024
INPUT_SAMPLE_RATE = 48000    # Input sample rate from audio device
WHISPER_SAMPLE_RATE = 16000  # Required sample rate for Whisper
SILENCE_THRESHOLD = 0.01     # Threshold to detect more audio
SILENCE_DURATION = 1.5      # Seconds of silence to trigger transcription
audio_queue = queue.Queue()
stop_flag = threading.Event()
recording_flag = threading.Event()
stream = None

def cleanup():
    """Cleanup function to ensure proper resource disposal"""
    global stream
    if stream is not None:
        stream.close()
    sd.stop()

atexit.register(cleanup)

def audio_callback(indata, frames, time, status):
    """Callback function to capture audio data."""
    if status:
        print(status)
    if recording_flag.is_set():
        max_val = np.max(np.abs(indata))
        if max_val > SILENCE_THRESHOLD:
            print(f"Audio level: {max_val:.3f}", end="\r")
        audio_queue.put(indata.copy())

def copy_to_clipboard(text):
    """Copies the given text to the clipboard."""
    try:
        pyperclip.copy(text)
        print("Text copied to clipboard.")
    except pyperclip.PyperclipException as e:
        print(f"Error copying to clipboard: {e}. Ensure you have xclip or xsel installed.")

def transcribe_audio():
    """Thread to transcribe audio in real time."""
    audio_buffer = []
    last_speech_time = time.time()
    transcribing = False

    while not stop_flag.is_set():
        try:
            audio_data = audio_queue.get(timeout=0.1)
            audio_buffer.append(audio_data)
            max_val = np.max(np.abs(audio_data))
            if max_val > SILENCE_THRESHOLD:
                last_speech_time = time.time()

            if time.time() - last_speech_time >= SILENCE_DURATION and len(audio_buffer) > 0:
                # Silence detected, process the audio
                transcribing = True
                concatenated_audio = np.concatenate(audio_buffer, axis=0)
                audio_data = concatenated_audio.flatten()
                max_volume = max(abs(audio_data.max()), abs(audio_data.min()))
                print(f"\nProcessing audio... (max volume: {max_volume:.3f})")

                try:
                    # Resample from 48kHz to 16kHz
                    audio_length = len(audio_data)
                    resampled_length = int(audio_length * WHISPER_SAMPLE_RATE / INPUT_SAMPLE_RATE)
                    resampled_audio = np.interp(
                        np.linspace(0, audio_length, resampled_length),
                        np.linspace(0, audio_length, audio_length),
                        audio_data
                    )

                    # Normalize audio
                    resampled_audio = resampled_audio.astype(np.float32)
                    if resampled_audio.max() > 1.0 or resampled_audio.min() < -1.0:
                        resampled_audio = resampled_audio / max(abs(resampled_audio.max()), abs(resampled_audio.min()))

                    result = model.transcribe(resampled_audio, language="en")
                    text = result['text'].strip()
                    if text:
                        print(f"\nTranscription: {text}")
                        copy_to_clipboard(text)
                    else:
                        print("\nNo speech detected in audio")
                except Exception as e:
                    print(f"\nTranscription error: {e}")

                # Clear the buffer
                audio_buffer = []
                last_speech_time = time.time()
                transcribing = False

        except queue.Empty:
            continue
        except Exception as e:
            print(f"Error in transcription thread: {e}")
            break

def audio_input_thread(device_idx, sample_rate):
    """Thread to handle audio input."""
    global stream
    try:
        stream = sd.InputStream(
            callback=audio_callback,
            channels=1,
            samplerate=INPUT_SAMPLE_RATE,
            blocksize=BUFFER_SIZE,
            device=device_idx,
            dtype=np.float32
        )
        with stream:
            print(f"Listening on device {device_idx} at {INPUT_SAMPLE_RATE} Hz... Press Ctrl+C to stop.")
            while not stop_flag.is_set():
                time.sleep(0.1)
    except Exception as e:
        print(f"Error in audio input thread: {e}")
        stop_flag.set()

def signal_handler(sig, frame):
    """Handles Ctrl+C signal."""
    print("\nStopping...")
    stop_flag.set()
    cleanup()
    sys.exit(0)

def toggle_recording():
    """Toggles the recording state."""
    if recording_flag.is_set():
        recording_flag.clear()
        print("Recording paused.")
    else:
        recording_flag.set()
        print("Recording started.")

if __name__ == "__main__":
    # List available audio devices
    print("Available audio devices:")
    devices = sd.query_devices()
    print(devices)

    # Set the signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Use the system default input device
    audio_device_idx = sd.default.device[0]  # [0] is input, [1] would be output
    device_info = sd.query_devices(audio_device_idx)

    print(f"Using default input device {audio_device_idx}: {device_info['name']}")

    # Start with recording paused
    print("Press Enter to start/stop recording.")

    try:
        # Start the transcription thread
        transcription_thread = threading.Thread(target=transcribe_audio, daemon=True)
        transcription_thread.start()

        # Start capturing audio from the microphone
        input_thread = threading.Thread(target=audio_input_thread,
                                     args=(audio_device_idx, INPUT_SAMPLE_RATE),
                                     daemon=True)
        input_thread.start()

        # Main loop - recording toggle
        while not stop_flag.is_set():
            user_input = input() # Wait for user input
            if user_input == "":
                toggle_recording() # Toggle recording on Enter
            elif user_input.lower() == "exit":
                break

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        stop_flag.set()
        cleanup()
        try:
            transcription_thread.join(timeout=1)
            input_thread.join(timeout=1)
        except:
            pass
        print("Stopped.")
