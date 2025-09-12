"""
Wan VACE Local Video Editing Node for ComfyUI
"""

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
from datetime import datetime

# Import the base class and COMFYUI_AVAILABLE flag
from ..core.base import WanAPIBase, COMFYUI_AVAILABLE

# Try to import folder_paths if available
try:
    import folder_paths
except ImportError:
    pass

class WanVACEVideoEdit(WanAPIBase):
    """Node for local video editing using Wan VACE model"""
    
    # Define available Wan VACE models
    MODEL_OPTIONS = [
        "wan2.1-vace-plus"    # Professional Edition
    ]
    
    # Define control conditions for local editing
    CONTROL_CONDITION_OPTIONS = [
        "",                   # No control condition
        "posebodyface",       # Extract facial expressions and body movements
        "posebody",           # Extract body movements only
        "depth",              # Extract composition and motion contours
        "scribble"            # Extract line art structure
    ]
    
    # Define mask types for local editing
    MASK_TYPE_OPTIONS = [
        "tracking",           # Dynamic tracking of the target object
        "fixed"               # Fixed mask area
    ]
    
    # Define expand modes for local editing
    EXPAND_MODE_OPTIONS = [
        "hull",               # Polygon mode
        "bbox",               # Bounding box mode
        "original"            # Raw mode
    ]
    
    # Define video resolutions
    RESOLUTION_OPTIONS = [
        "1280*720",           # 16:9 aspect ratio (default)
        "720*1280",           # 9:16 aspect ratio
        "960*960",            # 1:1 aspect ratio
        "832*1088",           # 3:4 aspect ratio
        "1088*832"            # 4:3 aspect ratio
    ]
    
    def __init__(self):
        super().__init__()
        # Use the centralized API endpoint from the base class
        # To use Mainland China region, modify API_ENDPOINT_POST_VIDEO in core/base.py
        self.api_url = self.API_ENDPOINT_POST_VIDEO
    
    @classmethod
    def INPUT_TYPES(cls):
        # Define output directory options
        if COMFYUI_AVAILABLE:
            # Use ComfyUI's output directory with browseable option
            output_dir_options = {
                "default": "./videos",
                "tooltip": "Directory where the generated video will be saved. Browse to select a custom directory."
            }
        else:
            # Fallback to string input
            output_dir_options = {
                "default": "./videos",
                "multiline": False
            }
            
        return {
            "required": {
                "model": (cls.MODEL_OPTIONS, {
                    "default": "wan2.1-vace-plus"
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "Edit the video with the following description"
                }),
                "video_url": ("STRING", {
                    "default": "",
                    "tooltip": "URL of the input video"
                })
            },
            "optional": {
                "ref_images_url": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Newline-separated URLs for reference images (only 1 image supported)"
                }),
                "mask_image_url": ("STRING", {
                    "default": "",
                    "tooltip": "URL of the mask image"
                }),
                "mask_frame_id": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 1000
                }),
                "mask_video_url": ("STRING", {
                    "default": "",
                    "tooltip": "URL of the mask video"
                }),
                "control_condition": (cls.CONTROL_CONDITION_OPTIONS, {
                    "default": ""
                }),
                "mask_type": (cls.MASK_TYPE_OPTIONS, {
                    "default": "tracking"
                }),
                "expand_ratio": ("FLOAT", {
                    "default": 0.05,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01
                }),
                "expand_mode": (cls.EXPAND_MODE_OPTIONS, {
                    "default": "hull"
                }),
                "size": (cls.RESOLUTION_OPTIONS, {
                    "default": "1280*720"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647
                }),
                "prompt_extend": ("BOOLEAN", {
                    "default": False
                }),
                "watermark": ("BOOLEAN", {
                    "default": False
                }),
                "output_dir": ("STRING", output_dir_options)
            }
        }
    
    RETURN_TYPES = ("STRING",)  # Returns path to downloaded video file
    FUNCTION = "generate"
    CATEGORY = "Ru4ls/Wan/VACE"
    
    def generate(self, model, prompt, video_url, ref_images_url="", mask_image_url="", 
                 mask_frame_id=1, mask_video_url="", control_condition="", mask_type="tracking",
                 expand_ratio=0.05, expand_mode="hull", size="1280*720", seed=0, 
                 prompt_extend=False, watermark=False, output_dir="./videos"):
        
        # Check API key
        self.check_api_key()
        
        # Prepare API payload
        payload = {
            "model": model,
            "input": {
                "function": "video_edit",
                "prompt": prompt,
                "video_url": video_url
            },
            "parameters": {
                "mask_type": mask_type,
                "expand_mode": expand_mode,
                "size": size,
                "prompt_extend": prompt_extend,
                "watermark": watermark
            }
        }
        
        # Add seed if provided
        if seed > 0:
            payload["parameters"]["seed"] = seed
            
        # Add control condition if provided
        if control_condition:
            payload["parameters"]["control_condition"] = control_condition
            
        # Add expand_ratio if not default
        if expand_ratio != 0.05:
            payload["parameters"]["expand_ratio"] = expand_ratio
            
        # Add mask_image_url if provided
        if mask_image_url:
            payload["input"]["mask_image_url"] = mask_image_url
            
        # Add mask_frame_id if not default
        if mask_frame_id != 1:
            payload["input"]["mask_frame_id"] = mask_frame_id
            
        # Add mask_video_url if provided
        if mask_video_url:
            payload["input"]["mask_video_url"] = mask_video_url
        
        # Handle ref_images_url as a list (only 1 image supported)
        if ref_images_url:
            ref_images_list = [url.strip() for url in ref_images_url.split('\n') if url.strip()]
            if ref_images_list:
                payload["input"]["ref_images_url"] = ref_images_list[:1]  # Only take the first image
        
        # Set headers according to DashScope documentation
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"  # Wan requires async processing
        }
        
        try:
            # Make API request
            print(f"Making API request to {self.api_url}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            response = requests.post(self.api_url, headers=headers, json=payload)
            print(f"Response status code: {response.status_code}")
            if hasattr(response, 'text'):
                print(f"Response text: {response.text[:500]}...")  # Print first 500 chars
            response.raise_for_status()
            
            # Parse response to get task_id
            result = response.json()
            print(f"API response received: {json.dumps(result, indent=2)[:200]}...")  # Print first 200 chars
            
            # Check if this is a task creation response
            if "output" in result and "task_id" in result["output"]:
                task_id = result["output"]["task_id"]
                task_status = result["output"]["task_status"]
                print(f"Task created with ID: {task_id}, status: {task_status}")
                
                # Now we need to poll for the result
                task_result = self.poll_task_result(task_id, output_dir)
                return (task_result,)  # Return path to downloaded video file
            else:
                raise ValueError(f"Unexpected API response format: {result}")
                
        except requests.exceptions.RequestException as e:
            # More detailed error handling
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                response_text = e.response.text
                print(f"API request failed with status {status_code}: {response_text}")
                if status_code == 401:
                    raise RuntimeError(f"API request failed: 401 Unauthorized. "
                                    f"This usually means your API key is invalid or not properly configured. "
                                    f"Error details: {response_text}")
                elif status_code == 403:
                    raise RuntimeError(f"API request failed: 403 Forbidden. "
                                    f"This usually means your API key is valid but you don't have access to this model. "
                                    f"Error details: {response_text}")
                elif status_code == 400:
                    raise RuntimeError(f"API request failed: 400 Bad Request. "
                                    f"This usually means there's an issue with the request format. "
                                    f"Error details: {response_text}")
                else:
                    raise RuntimeError(f"API request failed: {status_code} {e.response.reason}. Response: {response_text}")
            else:
                raise RuntimeError(f"API request failed: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to process API response: {str(e)}")
    
    def poll_task_result(self, task_id, output_dir="./videos"):
        """"Poll for task result until completion and download video"""
        import time
        
        # URL for querying task results
        # To use Mainland China region, modify API_ENDPOINT_GET in core/base.py
        query_url = self.API_ENDPOINT_GET.format(task_id=task_id)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        max_attempts = 60  # Maximum polling attempts (may take longer for video)
        attempt = 0
        
        while attempt < max_attempts:
            try:
                print(f"Polling task {task_id}, attempt {attempt + 1}/{max_attempts}")
                response = requests.get(query_url, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                task_status = result["output"]["task_status"]
                print(f"Task status: {task_status}")
                
                if task_status == "SUCCEEDED":
                    # Task completed successfully
                    if "video_url" in result["output"]:
                        video_url = result["output"]["video_url"]
                        
                        # Download the video
                        video_response = requests.get(video_url)
                        video_response.raise_for_status()
                        
                        # Create a unique filename for the video
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        video_filename = f"wan_vace_video_edit_{timestamp}.mp4"
                        
                        # Handle output directory based on ComfyUI availability
                        if COMFYUI_AVAILABLE and not output_dir.startswith(("./", "/")):
                            # Use ComfyUI's output directory structure
                            if output_dir.endswith("/"):
                                output_dir = output_dir[:-1]
                            full_output_folder = folder_paths.get_output_directory()
                            output_path = os.path.join(full_output_folder, output_dir)
                        else:
                            # Resolve output directory path (existing logic)
                            if output_dir.startswith("./"):
                                # Relative to the node directory
                                output_path = os.path.join(os.path.dirname(__file__), output_dir[2:])
                            else:
                                output_path = output_dir
                        
                        # Create output directory if it doesn't exist
                        os.makedirs(output_path, exist_ok=True)
                        
                        # Save video to file
                        video_path = os.path.join(output_path, video_filename)
                        with open(video_path, "wb") as f:
                            f.write(video_response.content)
                        
                        print(f"Video downloaded and saved to: {video_path}")
                        # Return path relative to ComfyUI output directory if using ComfyUI
                        if COMFYUI_AVAILABLE and not output_dir.startswith(("./", "/")):
                            return os.path.join(output_dir, video_filename) if output_dir != "./videos" else video_filename
                        else:
                            return video_path  # Return full path
                    else:
                        raise ValueError(f"Unexpected API response format: {result}")
                        
                elif task_status == "FAILED":
                    # Task failed
                    error_code = result["output"].get("code", "Unknown")
                    error_message = result["output"].get("message", "Unknown error")
                    raise RuntimeError(f"Task failed with code: {error_code}, message: {error_message}")
                    
                elif task_status in ["PENDING", "RUNNING"]:
                    # Task still in progress, wait and retry
                    time.sleep(10)  # Wait 10 seconds before retrying (video generation may take longer)
                    attempt += 1
                    continue
                    
                else:
                    raise ValueError(f"Unexpected task status: {task_status}")
                    
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"Failed to query task status: {str(e)}")
        
        # If we've reached here, we've exceeded max attempts
        raise RuntimeError(f"Task did not complete within the expected time ({max_attempts} attempts)")
