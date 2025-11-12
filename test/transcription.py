

from pyannote.audio import Pipeline
import whisper
import os

# Load Whisper
model = whisper.load_model("base")
transcription = model.transcribe("test1.mp3", verbose=False)

# Run diarization
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization",
    use_auth_token = os.getenv("HF_TOKEN")
)

diarization = pipeline("test1.mp3")

# Print diarized segments
for turn, _, speaker in diarization.itertracks(yield_label=True):
    print(f"{speaker}: {turn.start:.1f}s --> {turn.end:.1f}s")


'''
import whisper
from pyannote.audio import Pipeline
from datetime import timedelta

# Load Whisper model and transcribe audio
whisper_model = whisper.load_model("base")
whisper_result = whisper_model.transcribe("your_audio_file.mp3", verbose=False)

# Load PyAnnote pipeline
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization",
    use_auth_token="your_huggingface_token"
)

# Perform speaker diarization
diarization = pipeline("your_audio_file.mp3")

# Convert diarization segments to a list for easier handling
speaker_segments = list(diarization.itertracks(yield_label=True))

# Helper function to find the speaker for a given timestamp
def get_speaker_for_timestamp(timestamp):
    for segment, _, speaker in speaker_segments:
        if segment.start <= timestamp <= segment.end:
            return speaker, segment.start, segment.end
    return "Unknown", timestamp, timestamp

# Merge Whisper segments with speaker labels
merged_output = []

for segment in whisper_result['segments']:
    start = segment['start']
    end = segment['end']
    text = segment['text'].strip()

    speaker, s_start, s_end = get_speaker_for_timestamp((start + end) / 2)
    merged_output.append({
        "speaker": speaker,
        "start": s_start,
        "end": s_end,
        "text": text
    })

# Output nicely formatted transcript
for entry in merged_output:
    start_time = str(timedelta(seconds=int(entry['start'])))
    end_time = str(timedelta(seconds=int(entry['end'])))
    print(f"{entry['speaker']} [{start_time} - {end_time}]: {entry['text']}")

'''