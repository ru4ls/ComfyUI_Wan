import os
import json
import requests
from PIL import Image
import numpy as np
import torch
import io
import base64
from dotenv import load_dotenv
import sys
import pathlib

# Import ComfyUI's folder_paths for directory browsing
try:
    import folder_paths
    COMFYUI_AVAILABLE = True
except ImportError:
    COMFYUI_AVAILABLE = False
    print("folder_paths not available, using default directory handling")

# Load environment variables from .env file
# Try to load .env file from the current directory first
env_path = pathlib.Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Fallback to default behavior
    load_dotenv()

class WanAPIBase:
    """Base class for Wan API interactions"""
    
    # API endpoints - International region (default)
    # To use Mainland China region, change these URLs:
    # Video POST: https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis
    # II2V POST: https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis
    # T2I POST: https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis
    # GET: https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}
    API_ENDPOINT_POST_VIDEO = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"
    API_ENDPOINT_POST_II2V = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis"
    API_ENDPOINT_POST_T2I = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
    API_ENDPOINT_GET = "https://dashscope-intl.aliyuncs.com/api/v1/tasks/{task_id}"
    
    def __init__(self):
        self.api_key = os.getenv('DASHSCOPE_API_KEY')
        # Strip any extra quotes or whitespace
        if self.api_key:
            self.api_key = self.api_key.strip().strip('"\'')
        print(f"Initialized WanAPIBase with API key: {self.api_key[:8] if self.api_key else 'None'}...{self.api_key[-4:] if self.api_key else ''}")
        
    def check_api_key(self):
        """Check if API key is set in environment variables"""
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY environment variable not set. "
                             "Please set it before using this node.")
        return self.api_key
    
    def prepare_images(self, images):
        """Convert images to base64 strings for API submission"""
        image_data = []
        for i, image in enumerate(images, 1):
            if image is not None:
                # Convert tensor to PIL Image
                if isinstance(image, torch.Tensor):
                    # Convert tensor to numpy array
                    image_np = image.cpu().numpy()
                    # If the tensor is in [0, 1] range, convert to [0, 255]
                    if image_np.max() <= 1.0:
                        image_np = (image_np * 255).astype(np.uint8)
                    # If tensor has shape [H, W, C], convert to PIL
                    pil_image = Image.fromarray(image_np.squeeze())
                else:
                    pil_image = image
                
                # Convert PIL image to base64
                buffer = io.BytesIO()
                pil_image.save(buffer, format="PNG")
                img_str = base64.b64encode(buffer.getvalue()).decode()
                image_data.append({
                    "id": str(i),
                    "data": img_str
                })
        return image_data
