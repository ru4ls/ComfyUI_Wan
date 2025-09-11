"""
ComfyUI_Wan - A custom node for ComfyUI that integrates Wan models
for text-to-image generation.
"""

from .wan_nodes import WanT2IGenerator

NODE_CLASS_MAPPINGS = {
    "WanT2IGenerator": WanT2IGenerator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WanT2IGenerator": "Wan Text-to-Image Generator",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']