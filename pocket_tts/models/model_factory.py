"""
TTS Model Factory - creates appropriate TTS model based on configuration.
Supports both Pocket TTS (English) and Silero TTS (Russian).
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def create_tts_model(
    model_type: str = 'silero',
    language: str = 'ru',
    speaker: str = 'baya',
    device: str = 'cpu',
    **kwargs
):
    """
    Create TTS model based on type.

    Args:
        model_type: 'pocket' for Pocket TTS (English) or 'silero' for Silero TTS (Russian)
        language: Language code ('en' or 'ru')
        speaker: Speaker name (for Silero)
        device: Device to run on
        **kwargs: Additional parameters

    Returns:
        TTS model instance
    """
    if model_type.lower() == 'silero':
        logger.info(f"Creating Silero TTS model for {language}")
        from pocket_tts.models.silero_adapter import SileroAudiobookAdapter
        return SileroAudiobookAdapter.load_model(
            language=language,
            speaker=speaker,
            device=device,
            **kwargs
        )
    elif model_type.lower() == 'pocket':
        logger.info("Creating Pocket TTS model for English")
        from pocket_tts.models.tts_model import TTSModel
        return TTSModel.load_model(**kwargs)
    else:
        raise ValueError(f"Unknown model type: {model_type}. Use 'pocket' or 'silero'")


# Default to Silero for Russian
def load_default_model(**kwargs):
    """Load default TTS model (Silero for Russian)."""
    return create_tts_model(model_type='silero', **kwargs)
