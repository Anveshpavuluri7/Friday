import time
import sounddevice as sd
from openwakeword.model import Model

m = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
scores = []

def cb(indata, frames, time_info, status):
    try:
        prediction = m.predict(indata.flatten())
        sc = prediction.get('hey_jarvis_v0.1', 0)
        scores.append(sc)
        if sc > 0.5:
             print("HIGH SCORE!", sc)
    except Exception as e:
        print("Error:", e)

try:
    with sd.InputStream(samplerate=16000, channels=1, dtype='int16', blocksize=1280, callback=cb):
        print("Stream opened... waiting 3 seconds")
        time.sleep(3)
except Exception as e:
    print("Stream Error:", e)

print("Max score:", max(scores) if scores else "None")
print("Num frames:", len(scores))
