"""
Silero TTS Model Wrapper for Russian language support.
Replaces Pocket TTS with Silero TTS for Russian audiobook generation.
"""

import logging
import torch
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, Union
import soundfile as sf

logger = logging.getLogger(__name__)


class SileroTTSModel:
    """
    Wrapper for Silero TTS model to generate Russian speech.

    Compatible interface with original TTSModel for audiobook generation.
    """

    def __init__(
        self,
        language: str = 'ru',
        speaker: str = 'baya',
        device: str = 'cpu',
        sample_rate: int = 48000,
        **kwargs
    ):
        """
        Initialize Silero TTS model.

        Args:
            language: Language code ('ru' for Russian)
            speaker: Speaker name (baya, aidar, kseniya, xenia, eugene, random)
            device: Device to run on ('cpu' or 'cuda')
            sample_rate: Output sample rate (48000 default for Silero)
        """
        self.language = language
        self.speaker = speaker
        self._device = device
        self._sample_rate = sample_rate
        self.model = None
        self.has_voice_cloning = False  # Silero doesn't support voice cloning

        logger.info(f"Initializing Silero TTS: language={language}, speaker={speaker}, device={device}")
        self._load_model()

    def _load_model(self):
        """Load Silero TTS model from torch hub."""
        try:
            logger.info("Loading Silero TTS model from torch hub...")

            # Load Silero TTS model
            self.model, _ = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_tts',
                language=self.language,
                speaker='v3_1_ru'
            )

            self.model.to(self._device)
            logger.info("Silero TTS model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load Silero TTS model: {e}")
            raise RuntimeError(f"Could not load Silero TTS model: {e}")

    @property
    def device(self) -> str:
        """Get device type."""
        return self._device

    @property
    def sample_rate(self) -> int:
        """Get sample rate."""
        return self._sample_rate

    def generate(
        self,
        text: str,
        temperature: float = 0.7,
        speaker: Optional[str] = None,
        sample_rate: Optional[int] = None,
        **kwargs
    ) -> np.ndarray:
        """
        Generate speech from text.

        Args:
            text: Text to synthesize
            temperature: Sampling temperature (not used by Silero, kept for compatibility)
            speaker: Override default speaker
            sample_rate: Override default sample rate
            **kwargs: Additional parameters (for compatibility)

        Returns:
            Audio waveform as numpy array
        """
        if not self.model:
            raise RuntimeError("Model not loaded")

        if not text.strip():
            logger.warning("Empty text provided, returning silence")
            return np.zeros(int(0.5 * self._sample_rate), dtype=np.float32)

        try:
            # Use provided speaker or default
            spk = speaker or self.speaker
            sr = sample_rate or self._sample_rate

            # Generate audio
            logger.debug(f"Generating audio for text: {text[:50]}...")
            audio = self.model.apply_tts(
                text=text,
                speaker=spk,
                sample_rate=sr
            )

            # Convert to numpy array
            if isinstance(audio, torch.Tensor):
                audio = audio.cpu().numpy()

            # Ensure float32
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)

            logger.debug(f"Generated audio: shape={audio.shape}, duration={len(audio)/sr:.2f}s")
            return audio

        except Exception as e:
            logger.error(f"Failed to generate audio: {e}")
            # Return silence on error
            return np.zeros(int(0.5 * self._sample_rate), dtype=np.float32)

    def generate_with_emotions(
        self,
        text: str,
        emotion: str = 'neutral',
        temperature: float = 0.7,
        speed_factor: float = 1.0,
        **kwargs
    ) -> np.ndarray:
        """
        Generate speech with emotion parameters.

        Note: Silero doesn't directly support emotions, but we can adjust
        speed and other parameters to simulate emotional speech.

        Args:
            text: Text to synthesize
            emotion: Emotion type (for logging, not directly used)
            temperature: Temperature (kept for compatibility)
            speed_factor: Speed adjustment factor
            **kwargs: Additional parameters

        Returns:
            Audio waveform as numpy array
        """
        logger.debug(f"Generating with emotion: {emotion}, speed: {speed_factor}")

        # Generate base audio
        audio = self.generate(text, temperature=temperature, **kwargs)

        # Apply speed adjustment if needed
        if speed_factor != 1.0:
            audio = self._adjust_speed(audio, speed_factor)

        return audio

    def _adjust_speed(self, audio: np.ndarray, speed_factor: float) -> np.ndarray:
        """
        Adjust audio speed using simple resampling.

        Args:
            audio: Input audio
            speed_factor: Speed multiplier (>1 = faster, <1 = slower)

        Returns:
            Speed-adjusted audio
        """
        try:
            from scipy import signal

            # Calculate new length
            new_length = int(len(audio) / speed_factor)

            # Resample
            audio_adjusted = signal.resample(audio, new_length)

            return audio_adjusted.astype(np.float32)

        except ImportError:
            logger.warning("scipy not available, speed adjustment disabled")
            return audio
        except Exception as e:
            logger.warning(f"Speed adjustment failed: {e}")
            return audio

    def save_audio(self, audio: np.ndarray, output_path: Union[str, Path]) -> None:
        """
        Save audio to file.

        Args:
            audio: Audio waveform
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        sf.write(str(output_path), audio, self._sample_rate)
        logger.info(f"Audio saved to {output_path}")

    def get_available_speakers(self) -> list:
        """Get list of available speakers."""
        # Silero v3.1 Russian speakers
        return ['baya', 'aidar', 'kseniya', 'xenia', 'eugene', 'random']

    def set_speaker(self, speaker: str) -> None:
        """
        Change the default speaker.

        Args:
            speaker: Speaker name
        """
        available = self.get_available_speakers()
        if speaker not in available:
            logger.warning(f"Speaker '{speaker}' not in available list: {available}")

        self.speaker = speaker
        logger.info(f"Speaker changed to: {speaker}")

    def unload_model(self) -> None:
        """Unload model to free memory."""
        if self.model:
            del self.model
            self.model = None
            torch.cuda.empty_cache()
            logger.info("Silero TTS model unloaded")

    def reload_model(self) -> None:
        """Reload the model."""
        self.unload_model()
        self._load_model()

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            'model_type': 'Silero TTS',
            'language': self.language,
            'speaker': self.speaker,
            'device': self._device,
            'sample_rate': self._sample_rate,
            'has_voice_cloning': self.has_voice_cloning,
            'available_speakers': self.get_available_speakers()
        }

    def __repr__(self) -> str:
        return f"SileroTTSModel(language={self.language}, speaker={self.speaker}, device={self._device})"
