# transcription
# 
import whisper
import sounddevice as sd
import numpy as np
import cv2
import queue





model = whisper.load_model("small")

# Parameters for audio recording
SAMPLE_RATE = 16000  # Whisper's expected sample rate
BLOCK_SIZE = 4000    # Number of frames per block (to capture approximately 0.25s of audio)
CHANNELS = 1         # Number of audio channels

# Queue to hold audio data chunks
audio_queue = queue.Queue()
running = True

def audio_callback(indata, frames, time, status):
    """Callback function to process the audio stream."""
    if status:
        print(f"Status: {status}")
    audio_queue.put(indata.copy())

# Start the audio stream
stream = sd.InputStream(callback=audio_callback, channels=CHANNELS, samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE)
stream.start()

# Initialize audio buffer
audio_buffer = np.array([], dtype=np.float32)


# Start capturing video from the webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    running = False


with open ("transcripts.txt", "w") as file:
    file.writelines("\n")
try:
    while running:
        
        ret, frame = cap.read()
        '''if ret:
            cv2.imshow('Webcam Feed', frame)''' 
            # Doesn't show up the image from webcam, but very inefficient
            # Should utilize the same stream as the other file 
        

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # --- Audio Processing ---
        # Check if there's audio data available in the queue
        try:
            chunk = audio_queue.get_nowait()  # Non-blocking get
            audio_buffer = np.append(audio_buffer, chunk.flatten())

            # If we have enough audio, process it
            if len(audio_buffer) > SAMPLE_RATE * 5:  # Every 15 seconds
                # Transcribe using Whisper
                transcription = model.transcribe(audio_buffer, fp16=False)
                with open ("transcripts.txt", "a") as file:
                    file.writelines(transcription['text'] + "\n")
                    file.flush() 
                print("Transcription:", transcription['text'])
                
                # Reset the buffer after processing
                audio_buffer = np.array([], dtype=np.float32)

        except queue.Empty:
            # No audio data available in the queue right now
            pass

except KeyboardInterrupt:
    print("Stopping...")

# Release resources
running = False
stream.stop()
stream.close()
cap.release()
cv2.destroyAllWindows()

