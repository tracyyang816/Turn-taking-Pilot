import os
import time
import queue
import wave
import numpy as np
import sounddevice as sd
from openai import OpenAI


from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 4000  # ~0.25s
audio_queue = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    if status:
        print(status)
    audio_queue.put(indata.copy())

def write_wav(path, audio_f32, sr=16000):
    # clamp to [-1, 1] then convert to int16 PCM
    audio_f32 = np.clip(audio_f32, -1.0, 1.0)
    audio_i16 = (audio_f32 * 32767.0).astype(np.int16)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # int16
        wf.setframerate(sr)
        wf.writeframes(audio_i16.tobytes())

def transcribe_file(path):
    with open(path, "rb") as f:
        # pick one:
        # model="gpt-4o-mini-transcribe"
        # model="gpt-4o-transcribe"
        resp = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=f,
            # optional hints:
            # prompt="Two people discussing a robotics study. Terms: Mediapipe, DOA, gaze intervention."
        )
    return resp.text

stream = sd.InputStream(
    callback=audio_callback, channels=CHANNELS,
    samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE
)
stream.start()

audio_buffer = np.array([], dtype=np.float32)
WINDOW_SEC = 6
HOP_SEC = 3  # overlap

last_flush = time.time()

try:
    while True:
        try:
            chunk = audio_queue.get(timeout=0.1)
            audio_buffer = np.concatenate([audio_buffer, chunk.flatten()])
        except queue.Empty:
            pass

        now = time.time()
        if now - last_flush >= HOP_SEC and len(audio_buffer) >= SAMPLE_RATE * WINDOW_SEC:
            # take last WINDOW_SEC seconds
            segment = audio_buffer[-SAMPLE_RATE * WINDOW_SEC:]
            tmp_path = "tmp_chunk.wav"
            write_wav(tmp_path, segment, SAMPLE_RATE)

            text = transcribe_file(tmp_path)
            print(text)

            with open("transcripts.txt", "a") as f:
                f.write(text.strip() + "\n")

            last_flush = now

except KeyboardInterrupt:
    pass
finally:
    stream.stop()
    stream.close()
