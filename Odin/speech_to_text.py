"""
speech_to_text.py

Provides a simple helper to record audio from the default microphone
and transcribe it to text using the `speech_recognition` library.

Requirements:
- pip install SpeechRecognition
- A working microphone and a microphone backend (on Windows you may need to
  install PyAudio: `pip install pipwin` then `pipwin install pyaudio`, or use
  the `sounddevice`+`soundfile` combo with `pip install sounddevice soundfile`)

Functions:
- transcribe_from_microphone(...): records from the mic and returns text
- transcribe_audio(audio_data): transcribes an `sr.AudioData` object

Run as a script to test the microphone transcription.
"""

from typing import Optional
import speech_recognition as sr

# Module-level singleton — avoids re-creating the object on every call
_recognizer = sr.Recognizer()
# Track whether we've done the initial ambient noise calibration
_ambient_calibrated = False


def transcribe_audio(audio: sr.AudioData, language: str = "en-US") -> str:
    """Transcribe an sr.AudioData object to text using Google Web Speech API.

    Returns an empty string on unintelligible speech. Raises RuntimeError on
    API / request errors.
    """
    try:
        return _recognizer.recognize_google(audio, language=language)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        raise RuntimeError(f"Speech recognition request failed: {e}") from e


def transcribe_from_microphone(duration: Optional[float] = None,
                               timeout: Optional[float] = 5,
                               phrase_time_limit: Optional[float] = 10,
                               language: str = "en-US",
                               adjust_for_ambient: float = 1.0) -> str:
    """Record audio from the default microphone and return the transcribed text.

    Args:
        duration: If provided, record for exactly this many seconds. If None,
            use `listen()` which stops when speech ends (or when
            `phrase_time_limit` is reached).
        timeout: Maximum time to wait for the first phrase (seconds).
        phrase_time_limit: Maximum length of a phrase (seconds). Defaults to
            10 to prevent indefinite listening.
        language: Language code for recognition (default: "en-US").
        adjust_for_ambient: Seconds to adjust for ambient noise. Only applied
            once on the first call; subsequent calls reuse the cached level.

    Returns:
        Transcribed text (empty string if speech was unintelligible).

    Raises:
        RuntimeError: If the recognition API returns an error.
    """
    global _ambient_calibrated
    try:
        with sr.Microphone() as source:
            if not _ambient_calibrated:
                _recognizer.adjust_for_ambient_noise(source, duration=adjust_for_ambient)
                _ambient_calibrated = True
            if duration is not None:
                audio = _recognizer.record(source, duration=duration)
            else:
                try:
                    audio = _recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                except sr.WaitTimeoutError:
                    return "wait_timeout"
    except Exception as e:
        raise RuntimeError(f"Microphone error: {e}") from e

    return transcribe_audio(audio, language=language)
