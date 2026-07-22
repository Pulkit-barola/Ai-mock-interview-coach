import os
import io
import logging
from gtts import gTTS
import google.generativeai as genai

logger = logging.getLogger(__name__)

class VoiceInterviewManager:
    """Manages audio transcription using Gemini's native audio capability, and Text-to-Speech using gTTS."""

    def __init__(self, api_key=None):
        from utils.helpers import get_gemini_api_key
        self.api_key = api_key or get_gemini_api_key()
        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            logger.warning("Gemini API Key is not set. VoiceInterviewManager will fail until API is configured.")

    def text_to_speech_bytes(self, text):
        """Converts text to speech and returns raw audio bytes in MP3 format using gTTS."""
        try:
            if not text.strip():
                return None
            
            tts = gTTS(text=text, lang="en", slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            audio_bytes = fp.read()
            logger.info("Successfully converted text to speech bytes.")
            return audio_bytes
        except Exception as e:
            logger.error(f"Error in Text-to-Speech conversion: {e}", exc_info=True)
            return None

    def transcribe_audio_bytes(self, audio_bytes, mime_type="audio/wav"):
        """Transcribes audio bytes directly using Gemini's multimodal capabilities.
        
        This uses inline audio submission, which avoids the overhead of uploading files to the Gemini File API.
        """
        if not self.api_key:
            from utils.helpers import get_gemini_api_key
            self.api_key = get_gemini_api_key()
            if not self.api_key:
                raise ValueError("Gemini API Key is not configured.")
            genai.configure(api_key=self.api_key)

        # Map typical browser audio formats to valid Gemini mime types if necessary
        # Gemini accepts: audio/wav, audio/mp3, audio/ogg, audio/webm, audio/flac, etc.
        valid_mime = mime_type
        if "webm" in mime_type:
            valid_mime = "audio/webm"
        elif "wav" in mime_type or "x-wav" in mime_type:
            valid_mime = "audio/wav"
        elif "ogg" in mime_type:
            valid_mime = "audio/ogg"
        elif "mpeg" in mime_type or "mp3" in mime_type:
            valid_mime = "audio/mp3"

        prompt = (
            "Please listen to this audio clip and transcribe the speaker's words. "
            "Return only the exact transcript as plain text. Do not add comments, headers, "
            "or corrections. If the audio contains only silence or static, return '[No clear audio detected]'."
        )

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                contents=[
                    {
                        "mime_type": valid_mime,
                        "data": audio_bytes
                    },
                    prompt
                ]
            )
            
            transcript = response.text.strip()
            logger.info("Successfully transcribed audio using Gemini.")
            return transcript
        except Exception as e:
            logger.error(f"Error transcribing audio with Gemini: {e}", exc_info=True)
            # Try speech_recognition library as a fallback if installed and WAV format
            return self._fallback_transcription(audio_bytes, valid_mime)

    def _fallback_transcription(self, audio_bytes, mime_type):
        """Fallback transcription method using SpeechRecognition on the server side."""
        try:
            import speech_recognition as sr
            
            # SpeechRecognition requires WAV format
            if "wav" not in mime_type:
                logger.warning(f"Fallback transcription failed: format {mime_type} is not WAV.")
                return "Error: Could not transcribe this audio format. Please retry or enter answer via text."

            r = sr.Recognizer()
            audio_file = io.BytesIO(audio_bytes)
            with sr.AudioFile(audio_file) as source:
                audio_data = r.record(source)
            
            text = r.recognize_google(audio_data)
            logger.info("Fallback transcription completed successfully.")
            return text
        except Exception as fe:
            logger.error(f"Fallback transcription failed: {fe}")
            return "Error: Speech transcription service is temporarily unavailable. Please type your answer."
