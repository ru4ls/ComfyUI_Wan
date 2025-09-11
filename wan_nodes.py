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

# Debug: Print environment variable status
api_key = os.getenv('DASHSCOPE_API_KEY')
if api_key:
    # Strip any extra quotes or whitespace
    api_key = api_key.strip().strip('"\'')
    print(f"API Key loaded: {api_key[:8]}...{api_key[-4:]}")  # Print partial key for security
else:
    print("API Key not found in environment variables")


class WanAPIBase:
    """Base class for Wan API interactions"""
    
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


class WanT2IGenerator(WanAPIBase):
    """Node for text-to-image generation using Wan model"""
    
    # Define available Wan models
    MODEL_OPTIONS = [
        "wan2.2-t2i-flash",  # Speed Edition
        "wan2.2-t2i-plus"    # Professional Edition
    ]
    
    # Define allowed sizes for Wan models with descriptive names
    # Based on the documentation, Wan supports sizes from 512 to 1440 pixels
    SIZE_OPTIONS = [
        "1024*1024",  # 1:1 square (default)
        "1152*896",   # 9:7 landscape
        "896*1152",   # 7:9 portrait
        "1280*720",   # 16:9 landscape
        "720*1280",   # 9:16 portrait
        "1440*512",   # Wide landscape
        "512*1440"    # Tall portrait
    ]
    
    def __init__(self):
        super().__init__()
        self.api_url = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
        self.model = "wan2.2-t2i-flash"  # Using Wan Speed Edition as default
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (cls.MODEL_OPTIONS, {
                    "default": "wan2.2-t2i-flash"
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "Generate an image of a cat"
                }),
                "size": (cls.SIZE_OPTIONS, {
                    "default": "1024*1024"
                })
            },
            "optional": {
                "negative_prompt": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "prompt_extend": ("BOOLEAN", {
                    "default": True
                }),
                "watermark": ("BOOLEAN", {
                    "default": False
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647
                })
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"
    CATEGORY = "Ru4ls/Wan"
    
    def generate(self, model, prompt, size, negative_prompt="", prompt_extend=True, watermark=False, seed=0):
        # Check API key
        self.check_api_key()
        
        # Set the selected model
        self.model = model
        
        # Debug: Print API key status
        print(f"Using API key: {self.api_key[:8]}...{self.api_key[-4:] if self.api_key else 'None'}")
        print(f"Selected model: {self.model}")
        print(f"Using API endpoint: {self.api_url}")
        
        # Prepare API payload for text-to-image generation - using the Wan format
        payload = {
            "model": self.model,
            "input": {
                "prompt": prompt
            },
            "parameters": {
                "size": size,
                "prompt_extend": prompt_extend,
                "watermark": watermark,
                "n": 1  # Generate only one image
            }
        }
        
        # Add optional parameters if they have non-default values
        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt
        if seed > 0:
            payload["parameters"]["seed"] = seed
        
        # Set headers according to DashScope documentation
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"  # Wan requires async processing
        }
        
        # Debug: Print request details
        print(f"Request headers: {{'Authorization': 'Bearer {self.api_key[:8]}...', 'Content-Type': 'application/json', 'X-DashScope-Async': 'enable'}}")
        print(f"Request payload model: {payload['model']}")
        print(f"Request payload prompt: {payload['input']['prompt'][:100]}...")
        print(f"Request payload size: {payload['parameters']['size']}")
        print(f"Request payload prompt_extend: {payload['parameters']['prompt_extend']}")
        print(f"Request payload watermark: {payload['parameters']['watermark']}")
        
        try:
            # Make API request
            print(f"Making API request to {self.api_url}")
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
                task_result = self.poll_task_result(task_id)
                return task_result
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
    
    def poll_task_result(self, task_id):
        """Poll for task result until completion"""
        import time
        
        # URL for querying task results
        query_url = f"https://dashscope-intl.aliyuncs.com/api/v1/tasks/{task_id}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        max_attempts = 30  # Maximum polling attempts
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
                    results = result["output"]["results"]
                    if len(results) > 0 and "url" in results[0]:
                        image_url = results[0]["url"]
                        # Download the generated image
                        image_response = requests.get(image_url)
                        image_response.raise_for_status()
                        
                        # Convert to tensor
                        image = Image.open(io.BytesIO(image_response.content))
                        image_tensor = torch.from_numpy(np.array(image).astype(np.float32) / 255.0)
                        image_tensor = image_tensor.unsqueeze(0)  # Add batch dimension
                        
                        return (image_tensor,)
                    else:
                        raise ValueError(f"Unexpected API response format: {result}")
                        
                elif task_status == "FAILED":
                    # Task failed
                    error_code = result["output"].get("code", "Unknown")
                    error_message = result["output"].get("message", "Unknown error")
                    raise RuntimeError(f"Task failed with code: {error_code}, message: {error_message}")
                    
                elif task_status in ["PENDING", "RUNNING"]:
                    # Task still in progress, wait and retry
                    time.sleep(5)  # Wait 5 seconds before retrying
                    attempt += 1
                    continue
                    
                else:
                    raise ValueError(f"Unexpected task status: {task_status}")
                    
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"Failed to query task status: {str(e)}")
        
        # If we've reached here, we've exceeded max attempts
        raise RuntimeError(f"Task did not complete within the expected time ({max_attempts} attempts)")


class WanI2VGenerator(WanAPIBase):
    """Node for image-to-video generation using Wan model"""
    
    # Define available Wan i2v models
    MODEL_OPTIONS = [
        "wan2.2-i2v-flash",  # Speed Edition
        "wan2.2-i2v-plus"    # Professional Edition
    ]
    
    # Define allowed resolutions for Wan i2v models (using uppercase P as required by API)
    RESOLUTION_OPTIONS = [
        "480P",
        "720P",
        "1080P"
    ]
    
    def __init__(self):
        super().__init__()
        self.api_url = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"
    
    @classmethod
    def INPUT_TYPES(cls):
        # Define output directory options
        if COMFYUI_AVAILABLE:
            # Use ComfyUI's output directory with browseable option
            output_dir_options = {
                "default": "videos/",
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
                    "default": "wan2.2-i2v-flash"
                }),
                "image_url": ("STRING", {
                    "default": "https://example.com/your_image.png"
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "A cat running on the grass"
                })
            },
            "optional": {
                "negative_prompt": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "resolution": (cls.RESOLUTION_OPTIONS, {
                    "default": "720P"
                }),
                "prompt_extend": ("BOOLEAN", {
                    "default": True
                }),
                "watermark": ("BOOLEAN", {
                    "default": False
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647
                }),
                "output_dir": ("STRING", output_dir_options)
            }
        }
    
    RETURN_TYPES = ("STRING",)  # Returns path to downloaded video file
    FUNCTION = "generate"
    CATEGORY = "Ru4ls/Wan"
    
    def generate(self, model, image_url, prompt, negative_prompt="", resolution="720p", 
                 prompt_extend=True, watermark=False, seed=0, output_dir="videos/"):
        # Check API key
        self.check_api_key()
        
        # Prepare API payload for image-to-video generation
        payload = {
            "model": model,
            "input": {
                "prompt": prompt,
                "img_url": image_url
            },
            "parameters": {
                "resolution": resolution,
                "prompt_extend": prompt_extend,
                "watermark": watermark
            }
        }
        
        # Add optional parameters if they have non-default values
        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt
        if seed > 0:
            payload["parameters"]["seed"] = seed
        
        # Set headers according to DashScope documentation
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"  # Wan requires async processing
        }
        
        try:
            # Make API request
            print(f"Making API request to {self.api_url}")
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
    
    def poll_task_result(self, task_id, output_dir="videos/"):
        """Poll for task result until completion and download video"""
        import time
        import os
        from datetime import datetime
        
        # URL for querying task results
        query_url = f"https://dashscope-intl.aliyuncs.com/api/v1/tasks/{task_id}"
        
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
                        video_filename = f"wan_i2v_{timestamp}.mp4"
                        
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
                            return os.path.join(output_dir, video_filename) if output_dir != "videos/" else video_filename
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


# Node class mappings are in __init__.py