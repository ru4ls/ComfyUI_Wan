"""
Backward compatibility module - imports all Wan nodes from their separate modules.
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

__all__ = ['WanT2IGenerator', 'WanI2VGenerator', 'WanI2VEffectGenerator', 'WanT2VGenerator', 'WanII2VGenerator', 
           'WanVACEImageReference', 'WanVACEVideoRepainting', 'WanVACEVideoEdit', 
           'WanVACEVideoExtension', 'WanVACEVideoOutpainting']