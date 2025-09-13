"""
Wan VACE Video Extension Node for ComfyUI
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

class WanVACEVideoExtension(WanAPIBase):
    """Node for video extension using Wan VACE model"""
    
    # Define available Wan VACE models
    MODEL_OPTIONS = [
        "wan2.1-vace-plus"    # Professional Edition
    ]
    
    # Define control conditions for video extension
    CONTROL_CONDITION_OPTIONS = [
        "",                   # No control condition
        "posebodyface",       # Extract facial expressions and body movements
        "posebody",           # Extract body movements only
        "depth",              # Extract composition and motion contours
        "scribble"            # Extract line art structure
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
                    "default": "Extend the video with the following description"
                })
            },
            "optional": {
                "first_frame_url": ("STRING", {
                    "default": "",
                    "tooltip": "URL of the first frame image"
                }),
                "last_frame_url": ("STRING", {
                    "default": "",
                    "tooltip": "URL of the last frame image"
                }),
                "first_clip_url": ("STRING", {
                    "default": "",
                    "tooltip": "URL of the first video segment"
                }),
                "last_clip_url": ("STRING", {
                    "default": "",
                    "tooltip": "URL of the last video segment"
                }),
                "video_url": ("STRING", {
                    "default": "",
                    "tooltip": "URL of the reference video for motion features"
                }),
                "control_condition": (cls.CONTROL_CONDITION_OPTIONS, {
                    "default": ""
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
    
    RETURN_TYPES = ("STRING", "STRING")  # Returns path to downloaded video file and video URL
    RETURN_NAMES = ("video_file_path", "video_url")
    FUNCTION = "generate"
    CATEGORY = "Ru4ls/Wan/VACE"
    
    def generate(self, model, prompt, first_frame_url="", last_frame_url="", 
                 first_clip_url="", last_clip_url="", video_url="", control_condition="",
                 seed=0, prompt_extend=False, watermark=False, output_dir="./videos"):
        
        # Check API key
        self.check_api_key()
        
        # Prepare API payload
        payload = {
            "model": model,
            "input": {
                "function": "video_extension",
                "prompt": prompt
            },
            "parameters": {
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
            
        # Add first_frame_url if provided
        if first_frame_url:
            payload["input"]["first_frame_url"] = first_frame_url
            
        # Add last_frame_url if provided
        if last_frame_url:
            payload["input"]["last_frame_url"] = last_frame_url
            
        # Add first_clip_url if provided
        if first_clip_url:
            payload["input"]["first_clip_url"] = first_clip_url
            
        # Add last_clip_url if provided
        if last_clip_url:
            payload["input"]["last_clip_url"] = last_clip_url
            
        # Add video_url if provided
        if video_url:
            payload["input"]["video_url"] = video_url
        
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
                return task_result  # Return both path to downloaded video file and video URL
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
        """Poll for task result until completion and download video"""
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
                        video_filename = f"wan_vace_video_extension_{timestamp}.mp4"
                        
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
                            return_path = os.path.join(output_dir, video_filename) if output_dir != "./videos" else video_filename
                        else:
                            return_path = video_path  # Return full path
                        # Return both the file path and the video URL
                        return (return_path, video_url)
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
