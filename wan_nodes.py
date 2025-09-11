"""
Backward compatibility module - imports all Wan nodes from their separate modules.
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

__all__ = ['WanT2IGenerator', 'WanI2VGenerator', 'WanT2VGenerator', 'WanII2VGenerator', 
           'WanVACEImageReference', 'WanVACEVideoRepainting', 'WanVACEVideoEdit', 
           'WanVACEVideoExtension', 'WanVACEVideoOutpainting']