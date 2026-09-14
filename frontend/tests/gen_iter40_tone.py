import math
import wave
import struct


def main():
    sr = 48000
    duration = 6.0
    freq = 440.0
    amplitude = 0.25
    total = int(sr * duration)
    out = "/app/test_reports/iter40_tone.wav"
    with wave.open(out, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        for i in range(total):
            sample = amplitude * math.sin(2 * math.pi * freq * (i / sr))
            wf.writeframes(struct.pack("<h", int(max(-1.0, min(1.0, sample)) * 32767)))


if __name__ == "__main__":
    main()