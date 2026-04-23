"""
Adapter to integrate Silero TTS into the audiobook generation pipeline.
Provides compatibility layer between Silero and the existing audiobook generator.
"""

import logging
import numpy as np
import torch
from pathlib import Path
from typing import Optional, Dict, Any

from pocket_tts.models.silero_tts_model import SileroTTSModel
from pocket_tts.preprocessing.schema import EmotionType

logger = logging.getLogger(__name__)


class SileroAudiobookAdapter:
    """
    Adapter to make Silero TTS compatible with audiobook generation pipeline.

    Maps emotion parameters to Silero TTS generation parameters.
    """

    def __init__(
        self,
        language: str = 'ru',
        speaker: str = 'baya',
        device: str = 'cpu',
        sample_rate: int = 48000
    ):
        """
        Initialize adapter with Silero TTS model.

        Args:
            language: Language code
            speaker: Speaker name
            device: Device to run on
            sample_rate: Output sample rate
        """
        self.model = SileroTTSModel(
            language=language,
            speaker=speaker,
            device=device,
            sample_rate=sample_rate
        )

        # Emotion to speed mapping (from config)
        self.emotion_speed_map = {
            EmotionType.JOY: 1.15,
            EmotionType.SADNESS: 0.85,
            EmotionType.SURPRISE: 1.10,
            EmotionType.FEAR: 0.90,
            EmotionType.ANGER: 1.10,
            EmotionType.NO_EMOTION: 1.0,
        }

        # Temperature property for compatibility (not used by Silero)
        self.temp = 0.7

    @classmethod
    def load_model(
        cls,
        language: str = 'ru',
        speaker: str = 'baya',
        device: str = 'cpu',
        sample_rate: int = 48000,
        **kwargs
    ):
        """
        Load Silero TTS model (compatible with TTSModel.load_model interface).

        Args:
            language: Language code ('ru' for Russian)
            speaker: Speaker name (baya, aidar, kseniya, xenia, eugene)
            device: Device to run on ('cpu' or 'cuda')
            sample_rate: Output sample rate
            **kwargs: Additional parameters (for compatibility, ignored)

        Returns:
            SileroAudiobookAdapter: Initialized adapter with loaded model
        """
        logger.info(f"Loading Silero TTS model: language={language}, speaker={speaker}")
        return cls(
            language=language,
            speaker=speaker,
            device=device,
            sample_rate=sample_rate
        )

    def get_state_for_audio_prompt(self, audio_path: str, truncate: bool = True):
        """
        Get voice state from audio prompt (for compatibility).

        Note: Silero doesn't support voice cloning, so this returns None.
        The speaker is set during model initialization.

        Args:
            audio_path: Path to audio file (ignored)
            truncate: Whether to truncate (ignored)

        Returns:
            None (Silero uses speaker name instead of voice state)
        """
        logger.warning("Silero TTS doesn't support voice cloning. Using default speaker.")
        return None

    def generate_audio(
        self,
        voice_state,
        text: str,
        frames_after_eos: int = 0,
        **kwargs
    ) -> torch.Tensor:
        """
        Generate audio from text (compatible with TTSModel interface).

        Args:
            voice_state: Voice state (ignored for Silero)
            text: Text to synthesize
            frames_after_eos: Frames after end of sequence (for pause, converted to ms)
            **kwargs: Additional parameters

        Returns:
            Audio waveform as PyTorch tensor
        """
        # Generate audio
        audio = self.model.generate(text, **kwargs)

        # Add trailing silence if frames_after_eos specified
        if frames_after_eos > 0:
            # Convert frames to samples (assuming ~50 frames per second)
            pause_ms = frames_after_eos * 20  # Rough conversion
            pause_samples = int(pause_ms * self.model.sample_rate / 1000)
            silence = np.zeros(pause_samples, dtype=np.float32)
            audio = np.concatenate([audio, silence])

        # Convert numpy array to PyTorch tensor
        audio_tensor = torch.from_numpy(audio).float()
        return audio_tensor

    def generate_chunk(
        self,
        text: str,
        emotion: EmotionType,
        temperature: float = 0.7,
        tts_params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> np.ndarray:
        """
        Generate audio for a single chunk with emotion parameters.

        Args:
            text: Text to synthesize
            emotion: Detected emotion
            temperature: Temperature parameter (for compatibility)
            tts_params: Additional TTS parameters
            **kwargs: Additional parameters

        Returns:
            Audio waveform as numpy array
        """
        # Get speed factor for emotion
        speed_factor = self.emotion_speed_map.get(emotion, 1.0)

        # Override with explicit speed_factor if provided
        if tts_params and 'speed_factor' in tts_params:
            speed_factor = tts_params['speed_factor']

        logger.debug(f"Generating chunk: emotion={emotion.value}, speed={speed_factor}")

        # Generate audio with emotion parameters
        audio = self.model.generate_with_emotions(
            text=text,
            emotion=emotion.value,
            temperature=temperature,
            speed_factor=speed_factor,
            **kwargs
        )

        return audio

    def generate_with_pause(
        self,
        text: str,
        emotion: EmotionType,
        pause_duration_ms: int = 0,
        **kwargs
    ) -> np.ndarray:
        """
        Generate audio with trailing pause.

        Args:
            text: Text to synthesize
            emotion: Detected emotion
            pause_duration_ms: Pause duration in milliseconds
            **kwargs: Additional parameters

        Returns:
            Audio waveform with pause
        """
        # Generate main audio
        audio = self.generate_chunk(text, emotion, **kwargs)

        # Add pause if needed
        if pause_duration_ms > 0:
            pause_samples = int(pause_duration_ms * self.model.sample_rate / 1000)
            pause = np.zeros(pause_samples, dtype=np.float32)
            audio = np.concatenate([audio, pause])

        return audio

    def save_chunk(
        self,
        audio: np.ndarray,
        output_path: Path,
        chunk_index: int
    ) -> None:
        """
        Save audio chunk to file.

        Args:
            audio: Audio waveform
            output_path: Output directory
            chunk_index: Chunk number
        """
        output_file = output_path / f"chunk_{chunk_index:04d}.wav"
        self.model.save_audio(audio, output_file)

    @property
    def sample_rate(self) -> int:
        """Get sample rate."""
        return self.model.sample_rate

    @property
    def device(self) -> str:
        """Get device."""
        return self.model.device

    def set_speaker(self, speaker: str) -> None:
        """Change speaker."""
        self.model.set_speaker(speaker)

    def get_available_speakers(self) -> list:
        """Get available speakers."""
        return self.model.get_available_speakers()

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return self.model.get_model_info()

    def unload_model(self) -> None:
        """Unload model."""
        self.model.unload_model()

    def reload_model(self) -> None:
        """Reload model."""
        self.model.reload_model()
