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

# Import the base class
from .wan_base import WanAPIBase, COMFYUI_AVAILABLE

# Try to import folder_paths if available
try:
    import folder_paths
except ImportError:
    pass

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
        # Use the centralized API endpoint from the base class
        # To use Mainland China region, modify API_ENDPOINT_POST_T2I in wan_base.py
        self.api_url = self.API_ENDPOINT_POST_T2I
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
        # To use Mainland China region, modify API_ENDPOINT_GET in wan_base.py
        query_url = self.API_ENDPOINT_GET.format(task_id=task_id)
        
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