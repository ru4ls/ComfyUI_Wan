"""
ComfyUI_Wan - A custom node for ComfyUI that integrates Wan models
for text-to-image and image-to-video generation.
"""

from .wan_nodes import WanT2IGenerator, WanI2VGenerator

NODE_CLASS_MAPPINGS = {
    "WanT2IGenerator": WanT2IGenerator,
    "WanI2VGenerator": WanI2VGenerator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WanT2IGenerator": "Wan Text-to-Image Generator",
    "WanI2VGenerator": "Wan Image-to-Video Generator",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']