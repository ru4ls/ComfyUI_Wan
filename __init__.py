"""
ComfyUI_Wan - A custom node for ComfyUI that integrates Wan models
for text-to-image, image-to-video, and text-to-video generation.
"""

from .wan_t2i import WanT2IGenerator
from .wan_i2v import WanI2VGenerator
from .wan_t2v import WanT2VGenerator
from .wan_ii2v import WanII2VGenerator
from .wan_vace_image_reference import WanVACEImageReference
from .wan_vace_video_repainting import WanVACEVideoRepainting
from .wan_vace_video_edit import WanVACEVideoEdit
from .wan_vace_video_extension import WanVACEVideoExtension
from .wan_vace_video_outpainting import WanVACEVideoOutpainting

NODE_CLASS_MAPPINGS = {
    "WanT2IGenerator": WanT2IGenerator,
    "WanI2VGenerator": WanI2VGenerator,
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
    "WanT2VGenerator": "Wan Text-to-Video Generator",
    "WanII2VGenerator": "Wan Image-to-Video (First/Last Frame) Generator",
    "WanVACEImageReference": "Wan VACE - Multi-Image Reference",
    "WanVACEVideoRepainting": "Wan VACE - Video Repainting",
    "WanVACEVideoEdit": "Wan VACE - Local Video Editing",
    "WanVACEVideoExtension": "Wan VACE - Video Extension",
    "WanVACEVideoOutpainting": "Wan VACE - Video Outpainting",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

