#!/usr/bin/env python
"""test_audio.py - quick PyAudio check for Termux.

1. lists host APIs and devices
2. plays a 1 second 440 Hz tone on the speaker
3. records 3 seconds from the mic (and saves test_recording.wav)
4. plays the recording back

Options:
  --list         only list devices
  --no-play      skip the tone
  --no-record    skip mic test
  --seconds N    record length (default 3)
  --rate R       force a sample rate (default: try device default, 48000, 44100, 16000)
  --input  IDX   input device index
  --output IDX   output device index
"""

import argparse
import array
import math
import sys
import time
import wave

try:
    import pyaudio
except ImportError as e:  # pragma: no cover
    print("[x] Could not import PyAudio: %s" % e)
    print("    Install it with: bash install.sh   (or see README)")
    print("    PyAudio import nahi hua - pehle install.sh chalao.")
    sys.exit(1)

FORMAT = pyaudio.paInt16
SAMPLE_WIDTH = 2
CHUNK = 1024


def ok(msg):
    print("\033[1;32m[+]\033[0m " + msg)


def warn(msg):
    print("\033[1;33m[!]\033[0m " + msg)


def err(msg):
    print("\033[1;31m[x]\033[0m " + msg)


def list_devices(p):
    print("PyAudio %s | %s" % (pyaudio.__version__, pyaudio.get_portaudio_version_text()))
    print("Host APIs:")
    for i in range(p.get_host_api_count()):
        h = p.get_host_api_info_by_index(i)
        print("  [%d] %s (devices: %d)" % (i, h["name"], h["deviceCount"]))
    n = p.get_device_count()
    print("Devices (%d):" % n)
    for i in range(n):
        d = p.get_device_info_by_index(i)
        print("  [%d] %-30s in:%d out:%d default_rate:%d" % (
            i, d["name"], d["maxInputChannels"], d["maxOutputChannels"],
            int(d["defaultSampleRate"])))
    for label, fn in (("default input ", p.get_default_input_device_info),
                      ("default output", p.get_default_output_device_info)):
        try:
            d = fn()
            print("  %s -> [%d] %s" % (label, d["index"], d["name"]))
        except (IOError, OSError):
            print("  %s -> NONE" % label)
    return n


def candidate_rates(p, dev_index, is_input, forced):
    if forced:
        return [forced]
    rates = []
    try:
        if dev_index is not None:
            d = p.get_device_info_by_index(dev_index)
        elif is_input:
            d = p.get_default_input_device_info()
        else:
            d = p.get_default_output_device_info()
        rates.append(int(d["defaultSampleRate"]))
    except (IOError, OSError):
        pass
    for r in (48000, 44100, 16000):
        if r not in rates:
            rates.append(r)
    return rates


def open_stream(p, is_input, dev_index, forced_rate, channels=1):
    last = None
    for rate in candidate_rates(p, dev_index, is_input, forced_rate):
        kw = dict(format=FORMAT, channels=channels, rate=rate,
                  frames_per_buffer=CHUNK)
        if is_input:
            kw["input"] = True
            if dev_index is not None:
                kw["input_device_index"] = dev_index
        else:
            kw["output"] = True
            if dev_index is not None:
                kw["output_device_index"] = dev_index
        try:
            return p.open(**kw), rate
        except (IOError, OSError, ValueError) as e:
            last = e
    raise OSError(str(last))


def tone(rate, seconds=1.0, freq=440.0, volume=0.5):
    n = int(rate * seconds)
    fade = int(rate * 0.01)
    buf = array.array("h")
    for i in range(n):
        env = min(1.0, i / fade, (n - i) / fade) if fade else 1.0
        buf.append(int(32767 * volume * env * math.sin(2 * math.pi * freq * i / rate)))
    return buf.tobytes()


def play_bytes(p, data, rate, out_idx):
    stream = p.open(format=FORMAT, channels=1, rate=rate, output=True,
                    output_device_index=out_idx, frames_per_buffer=CHUNK)
    try:
        step = CHUNK * SAMPLE_WIDTH
        for i in range(0, len(data), step):
            stream.write(data[i:i + step])
        time.sleep(0.2)
    finally:
        stream.stop_stream()
        stream.close()


def test_tone(p, out_idx, forced_rate):
    print("\n== Speaker test: 1s 440 Hz tone ==")
    try:
        stream, rate = open_stream(p, False, out_idx, forced_rate)
    except OSError as e:
        err("Could not open output: %s" % e)
        print("    - Is the phone muted / media volume 0?")
        print("    - Close other apps using audio, then retry.")
        print("    - Output khul nahi raha: volume check karo, dusre audio apps band karo.")
        return False
    try:
        data = tone(rate)
        step = CHUNK * SAMPLE_WIDTH
        for i in range(0, len(data), step):
            stream.write(data[i:i + step])
        time.sleep(0.2)
    finally:
        stream.stop_stream()
        stream.close()
    ok("Tone played at %d Hz sample rate. Did you hear a beep? (Beep suna?)" % rate)
    return True


def test_mic(p, in_idx, out_idx, seconds, forced_rate):
    print("\n== Mic test: recording %ds - speak now! (ab bolo!) ==" % seconds)
    try:
        stream, rate = open_stream(p, True, in_idx, forced_rate)
    except OSError as e:
        err("Could not open microphone: %s" % e)
        print("    Most likely Termux has no RECORD_AUDIO permission:")
        print("      1) Install the Termux:API app (same store as Termux, e.g. F-Droid)")
        print("      2) termux-microphone-record -d -l 1; sleep 2; termux-microphone-record -q")
        print("         -> tap 'Allow' (ya Settings > Apps > Termux > Permissions > Microphone)")
        print("      3) If PulseAudio holds the mic: bash start-audio.sh --no-mic   then retry")
        return False
    frames = []
    try:
        for _ in range(int(rate / CHUNK * seconds)):
            frames.append(stream.read(CHUNK, exception_on_overflow=False))
    except (IOError, OSError) as e:
        err("Error while recording: %s" % e)
        return False
    finally:
        stream.stop_stream()
        stream.close()
    data = b"".join(frames)

    samples = array.array("h")
    samples.frombytes(data)
    peak = max((abs(s) for s in samples), default=0)
    rms = math.sqrt(sum(s * s for s in samples) / len(samples)) if samples else 0
    print("    recorded %d bytes @ %d Hz, peak=%d rms=%.0f" % (len(data), rate, peak, rms))

    with wave.open("test_recording.wav", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(rate)
        wf.writeframes(data)
    ok("Saved test_recording.wav")

    if peak == 0:
        warn("Recording is pure silence (all zeros).")
        print("    - Mic permission missing, or another app/PulseAudio is holding the mic.")
        print("    - Try: bash start-audio.sh --no-mic  then run this test again.")
        print("    - Some phones (Xiaomi/Honor) block mic for background voice assistants; reboot helps.")
    elif peak < 300:
        warn("Very quiet recording - speak louder / closer to the mic.")

    print("\n== Playback of your recording ==")
    try:
        play_bytes(p, data, rate, out_idx)
        ok("Playback done. Apni awaaz sunai di?")
    except (IOError, OSError) as e:
        err("Playback failed: %s" % e)
        return False
    return peak > 0


def main():
    ap = argparse.ArgumentParser(description="PyAudio test for Termux")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--no-play", action="store_true")
    ap.add_argument("--no-record", action="store_true")
    ap.add_argument("--seconds", type=int, default=3)
    ap.add_argument("--rate", type=int, default=None)
    ap.add_argument("--input", type=int, default=None)
    ap.add_argument("--output", type=int, default=None)
    a = ap.parse_args()

    try:
        p = pyaudio.PyAudio()
    except Exception as e:  # noqa: BLE001
        err("PyAudio() failed to initialise PortAudio: %s" % e)
        sys.exit(2)

    results = {}
    try:
        n = list_devices(p)
        if a.list:
            return 0
        if n == 0:
            err("PortAudio sees no devices.")
            print("    Termux's portaudio needs its OpenSL ES backend (package revision from Oct 2024+).")
            print("    Run: pkg upgrade portaudio   then reinstall: FORCE_REBUILD=1 bash install.sh")
            return 1
        if not a.no_play:
            results["speaker"] = test_tone(p, a.output, a.rate)
        if not a.no_record:
            results["mic"] = test_mic(p, a.input, a.output, a.seconds, a.rate)
    finally:
        p.terminate()

    print("\n== Summary ==")
    for k, v in results.items():
        (ok if v else err)("%s: %s" % (k, "OK" if v else "FAILED"))
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
