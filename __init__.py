"""
ComfyUI_Wan - A custom node for ComfyUI that integrates Wan models
for text-to-image, image-to-video, text-to-video, first-last-frame-tovideo, and VACE generation.
"""

from .generators.t2i import WanT2IGenerator
from .generators.i2v import WanI2VGenerator
from .generators.i2v_effect import WanI2VEffectGenerator
from .generators.t2v import WanT2VGenerator
from .generators.ii2v import WanII2VGenerator
from .vace.image_reference import WanVACEImageReference
from .vace.video_repainting import WanVACEVideoRepainting
from .vace.video_edit import WanVACEVideoEdit
from .vace.video_extension import WanVACEVideoExtension
from .vace.video_outpainting import WanVACEVideoOutpainting

NODE_CLASS_MAPPINGS = {
    "WanT2IGenerator": WanT2IGenerator,
    "WanI2VGenerator": WanI2VGenerator,
    "WanI2VEffectGenerator": WanI2VEffectGenerator,
    "WanT2VGenerator": WanT2VGenerator,
    "WanII2VGenerator": WanII2VGenerator,
    "WanVACEImageReference": WanVACEImageReference,
    "WanVACEVideoRepainting": WanVACEVideoRepainting,
    "WanVACEVideoEdit": WanVACEVideoEdit,
    "WanVACEVideoExtension": WanVACEVideoExtension,
    "WanVACEVideoOutpainting": WanVACEVideoOutpainting,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WanT2IGenerator": "Wan Text-to-Image Generator",
    "WanI2VGenerator": "Wan Image-to-Video Generator",
    "WanI2VEffectGenerator": "Wan Image-to-Video Effect Generator",
    "WanT2VGenerator": "Wan Text-to-Video Generator",
    "WanII2VGenerator": "Wan Image-to-Video (First/Last Frame) Generator",
    "WanVACEImageReference": "Wan VACE - Multi-Image Reference",
    "WanVACEVideoRepainting": "Wan VACE - Video Repainting",
    "WanVACEVideoEdit": "Wan VACE - Local Video Editing",
    "WanVACEVideoExtension": "Wan VACE - Video Extension",
    "WanVACEVideoOutpainting": "Wan VACE - Video Outpainting",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

