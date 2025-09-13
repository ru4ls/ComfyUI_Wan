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
# Try multiple locations for the .env file:
# 1. config/.env (our preferred location)
# 2. .env in the project root (for backward compatibility)
# 3. Fallback to default behavior (current working directory)

# Check config/.env first (go up one level to project root, then into config)
env_path = pathlib.Path(__file__).parent.parent / 'config' / '.env'
if env_path.exists():
    print(f"Loading environment variables from: {env_path}")
    load_dotenv(dotenv_path=env_path)
else:
    # Check .env in project root (go up one level to project root)
    env_path = pathlib.Path(__file__).parent.parent / '.env'
    if env_path.exists():
        print(f"Loading environment variables from: {env_path}")
        load_dotenv(dotenv_path=env_path)
    else:
        # Fallback to default behavior
        print("No .env file found, using default environment variable loading")
        load_dotenv()

class WanAPIBase:
    """Base class for Wan API interactions"""
    
    # API endpoints for different regions
    ENDPOINTS = {
        "international": {
            "video_post": "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis",
            "ii2v_post": "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis",
            "t2i_post": "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
            "get": "https://dashscope-intl.aliyuncs.com/api/v1/tasks/{task_id}"
        },
        "mainland_china": {
            "video_post": "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis",
            "ii2v_post": "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis",
            "t2i_post": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
            "get": "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
        }
    }
    
    def __init__(self):
        # Load API keys for different regions
        self.api_key = os.getenv('DASHSCOPE_API_KEY')
        self.api_key_china = os.getenv('DASHSCOPE_API_KEY_CHINA')
        # Strip any extra quotes or whitespace
        if self.api_key:
            self.api_key = self.api_key.strip().strip('"\'')
        if self.api_key_china:
            self.api_key_china = self.api_key_china.strip().strip('"\'')
        print(f"Initialized WanAPIBase with API keys: international={self.api_key[:8] if self.api_key else 'None'}...{self.api_key[-4:] if self.api_key else ''}, china={self.api_key_china[:8] if self.api_key_china else 'None'}...{self.api_key_china[-4:] if self.api_key_china else ''}")
    
    def check_api_key(self, region="international"):
        """Check if appropriate API key is set in environment variables"""
        if region == "mainland_china" and self.api_key_china:
            return self.api_key_china
        elif self.api_key:
            return self.api_key
        else:
            raise ValueError("DASHSCOPE_API_KEY environment variable not set. "
                             "Please set it before using this node.")
    
    def get_api_endpoints(self, region="international"):
        """Get the appropriate API endpoints based on region"""
        return self.ENDPOINTS.get(region, self.ENDPOINTS["international"])
    
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
