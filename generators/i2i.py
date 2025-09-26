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

class WanI2IGenerator(WanAPIBase):
    """Node for image-to-image generation using Wan model"""
    
    # Define available Wan i2i models
    MODEL_OPTIONS = [
        "wan2.5-i2i-preview",  # Preview Edition
    ]
    
    # Define allowed sizes for Wan i2i models
    SIZE_OPTIONS = [
        "1024*1024",  # 1:1 square (default)
        "1152*896",   # 9:7 landscape
        "896*1152",   # 7:9 portrait
        "1280*720",   # 16:9 landscape
        "720*1280",   # 9:16 portrait
        "1440*512",   # Wide landscape
        "512*1440",   # Tall portrait
        "768*768",    # 1:1 square
        "1440*1440",  # 1:1 square
    ]
    
    # Define region options
    REGION_OPTIONS = [
        "international",
        "mainland_china"
    ]
    
    def __init__(self):
        super().__init__()
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (cls.MODEL_OPTIONS, {
                    "default": "wan2.5-i2i-preview"
                }),
                "image_url_1": ("STRING", {
                    "default": "https://example.com/your_image1.png"
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "Edit the image with the desired changes"
                }),
                "region": (cls.REGION_OPTIONS, {
                    "default": "international"
                })
            },
            "optional": {
                "image_url_2": ("STRING", {
                    "default": ""
                }),
                "negative_prompt": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "size": (cls.SIZE_OPTIONS, {
                    "default": "1024*1024"
                }),
                "watermark": ("BOOLEAN", {
                    "default": False
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647
                }),
                "num_images": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 4
                })
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")  # Returns image tensor and image URL
    RETURN_NAMES = ("image", "image_url")
    FUNCTION = "generate"
    CATEGORY = "Ru4ls/Wan"
    
    def generate(self, model, image_url_1, prompt, region, image_url_2="", negative_prompt="", size="1024*1024", 
                 watermark=False, seed=0, num_images=1):
        # Check API key based on region
        api_key = self.check_api_key(region)
        
        # Get the appropriate API endpoints based on region
        endpoints = self.get_api_endpoints(region)
        api_url = endpoints["i2i_post"]
        
        # Prepare images array - at least one image is required
        images = [image_url_1.strip()]
        if image_url_2 and image_url_2.strip():
            images.append(image_url_2.strip())
        
        # Prepare API payload for image-to-image generation
        payload = {
            "model": model,
            "input": {
                "prompt": prompt,
                "images": images
            },
            "parameters": {
                "size": size,
                "watermark": watermark,
                "n": num_images
            }
        }
        
        # Add optional parameters if they have non-default values
        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt
        if seed > 0:
            payload["parameters"]["seed"] = seed
        
        # Set headers according to DashScope documentation
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"  # Wan requires async processing
        }
        
        try:
            # Make API request
            print(f"Making API request to {api_url}")
            response = requests.post(api_url, headers=headers, json=payload)
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
                task_result = self.poll_task_result(task_id, region)
                return task_result  # Return both image tensor and image URL
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
    
    def poll_task_result(self, task_id, region):
        """Poll for task result until completion"""
        import time
        
        # Get the appropriate API endpoints based on region
        endpoints = self.get_api_endpoints(region)
        query_url = endpoints["get"].format(task_id=task_id)
        
        # Check API key based on region
        api_key = self.check_api_key(region)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
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
                        
                        # Return both the image tensor and the image URL
                        return (image_tensor, image_url)
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