import numpy as np
import sounddevice as sd
import whisper
from typing import Optional

# --- Constants ---
SAMPLE_RATE = 16000        # Whisper expects 16 kHz mono audio
CHUNK_DURATION = 0.1       # Seconds per read chunk (100 ms)
SILENCE_THRESHOLD = 0.015  # RMS energy below this = silence
SILENCE_DURATION = 2     # Seconds of silence before stopping

# --- Lazy-loaded model singleton ---
_model = None


def _get_model(model_name: str = "base.en"):
    global _model
    if _model is None:
        print(f"Loading Whisper model '{model_name}'...")
        _model = whisper.load_model(model_name)
        print("Whisper model ready.")
    return _model


def transcribe_audio(audio_np: np.ndarray, language: str = "en"):
    """Transcribe a numpy float32 audio array (16 kHz mono) to text.

    Args:
        audio_np: 1-D float32 numpy array of audio samples at 16 kHz.
        language: Language code for Whisper (e.g. 'en', 'es').

    Returns:
        Transcribed text, or empty string if nothing was detected.
    """
    model = _get_model()
    audio_np = audio_np.astype(np.float32)
    result = model.transcribe(audio_np, language=language, fp16=False)
    return result["text"].strip()


def _record_fixed(duration: float):
    """Record exactly `duration` seconds from the default microphone."""
    frames = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    return frames.flatten()


def _record_until_silence(
    timeout: float = 5.0,
    phrase_time_limit: float = 10.0,
):
    """Record from the microphone until silence is detected.

    Waits up to `timeout` seconds for speech to begin. Once speaking starts,
    records until `SILENCE_DURATION` seconds of quiet or `phrase_time_limit`
    seconds total, whichever comes first.

    Returns:
        Numpy array of audio, or None if no speech was detected before timeout.
    """
    chunk_size = int(SAMPLE_RATE * CHUNK_DURATION)
    max_silent_chunks = int(SILENCE_DURATION / CHUNK_DURATION)

    frames = []
    silent_chunks = 0
    speaking = False

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
        # --- Wait for speech to begin ---
        waited = 0.0
        while waited < timeout:
            chunk, _ = stream.read(chunk_size)
            rms = float(np.sqrt(np.mean(chunk ** 2)))
            waited += CHUNK_DURATION
            if rms > SILENCE_THRESHOLD:
                speaking = True
                frames.append(chunk.copy())
                break

        if not speaking:
            return None  # timeout — no speech detected

        # --- Record until silence or phrase limit ---
        elapsed = 0.0
        while elapsed < phrase_time_limit:
            chunk, _ = stream.read(chunk_size)
            rms = float(np.sqrt(np.mean(chunk ** 2)))
            elapsed += CHUNK_DURATION
            frames.append(chunk.copy())

            if rms < SILENCE_THRESHOLD:
                silent_chunks += 1
                if silent_chunks >= max_silent_chunks:
                    break
            else:
                silent_chunks = 0

    return np.concatenate(frames).flatten() if frames else None


def transcribe_from_microphone(
    duration: Optional[float] = None,
    timeout: Optional[float] = 10.0,
    phrase_time_limit: Optional[float] = 10.0,
    language: str = "en",
    model_name: str = "base.en",
    **_kwargs,  # accepts unused args for drop-in compatibility
):
    """Record from the microphone and return the transcribed text.

    Args:
        duration: If set, record for exactly this many seconds (fixed mode).
                  If None, use silence-detection to know when you've stopped
                  speaking (recommended).
        timeout: Seconds to wait for speech to begin before giving up.
        phrase_time_limit: Maximum recording length in seconds.
        language: Whisper language code (e.g. 'en', 'es', 'fr').
        model_name: Whisper model to use ('tiny.en', 'base.en', 'small.en', …).

    Returns:
        Transcribed text, 'wait_timeout' if no speech was heard, or '' on
        unintelligible audio.
    """
    # Ensure the model is loaded with the requested size
    global _model
    if _model is None:
        _get_model(model_name)

    if duration is not None:
        audio = _record_fixed(duration)
    else:
        audio = _record_until_silence(
            timeout=timeout,
            phrase_time_limit=phrase_time_limit,
        )
        if audio is None:
            return "wait_timeout"

    return transcribe_audio(audio, language=language)


# ---------------------------------------------------------------------------
# Quick test — run this file directly to verify your microphone works
# ---------------------------------------------------------------------------
#if __name__ == "__main__":
#    print("Speak now...")
#    text = transcribe_from_microphone()
#    print(f"Transcribed: {text}")