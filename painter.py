import os
import io
import base64
import requests
import json
from PIL import Image
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class StableDiffusionPainter:
    def __init__(self, output_directory="images"):
        """
        Initialize the painter with Stability AI API
        
        Args:
            output_directory (str): Directory to save generated images
        """
        self.output_directory = output_directory
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
            
        # Get API key from environment variable
        self.api_key = os.getenv("STABILITY_API_KEY")
        if not self.api_key:
            print("UYARI: STABILITY_API_KEY bulunamadı. .env dosyasında tanımlamanız gerekiyor.")
        
        # API endpoint
        self.api_host = 'https://api.stability.ai'
        self.engine_id = "stable-diffusion-xl-1024-v1-0"  # SDXL for high quality images
        
    def paint(self, prompt, negative_prompt="", width=1024, height=1024, 
              cfg_scale=7.0, steps=30):
        """
        Generate an image based on a text prompt using Stability AI API
        
        Args:
            prompt (str): Text prompt to generate image from
            negative_prompt (str): Text to avoid in the generated image
            width (int): Width of the output image
            height (int): Height of the output image
            cfg_scale (float): How strictly the diffusion process adheres to the prompt
            steps (int): Number of diffusion steps
        
        Returns:
            str: Path to the saved image file
        """
        if not self.api_key:
            print("API anahtarı olmadan görüntü oluşturulamaz")
            return None
            
        try:
            print(f"Görüntü oluşturuluyor: '{prompt[:50]}...'")
            
            # Prepare text_prompts for API request
            text_prompts = [
                {
                    "text": prompt,
                    "weight": 1.0
                }
            ]
            
            # Only add negative prompt if it's not empty
            if negative_prompt and negative_prompt.strip():
                text_prompts.append({
                    "text": negative_prompt,
                    "weight": -1.0
                })
            
            # Prepare the API request
            response = requests.post(
                f"{self.api_host}/v1/generation/{self.engine_id}/text-to-image",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "text_prompts": text_prompts,
                    "cfg_scale": cfg_scale,
                    "height": height,
                    "width": width,
                    "samples": 1,
                    "steps": steps,
                },
            )
            
            if response.status_code != 200:
                print(f"API hatası: {response.status_code}")
                print(response.text)
                return None
                
            data = response.json()
            
            # Get the image data
            for i, image in enumerate(data["artifacts"]):
                # Create a unique filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                img_filename = f"image_{timestamp}.png"
                img_path = os.path.join(self.output_directory, img_filename)
                
                # Save the image
                with open(img_path, "wb") as f:
                    f.write(base64.b64decode(image["base64"]))
                
                print(f"Görüntü kaydedildi: {img_path}")
                return img_path
                
        except Exception as e:
            print(f"Görüntü oluşturma hatası: {e}")
            return None
    
    def generate_image(self, prompt, negative_prompt="", width=1024, height=1024, 
                       cfg_scale=7.0, steps=30):
        """
        Generate an image based on a text prompt (legacy method)
        
        Returns:
            str: Path to the saved image file
        """
        # Simply call the paint method for compatibility
        return self.paint(
            prompt=prompt, 
            negative_prompt=negative_prompt, 
            width=width, 
            height=height, 
            cfg_scale=cfg_scale, 
            steps=steps
        )

# Example usage
if __name__ == "__main__":
    painter = StableDiffusionPainter()
    
    # Example prompt
    prompt = "A beautiful landscape with mountains and a lake at sunset"
    
    # Generate image
    image_path = painter.paint(prompt)
    
    if image_path:
        print(f"Görüntü başarıyla oluşturuldu: {image_path}")
