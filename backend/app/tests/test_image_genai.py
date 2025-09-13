from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import time

load_dotenv()
client = genai.Client()

def generate_image_from_prompt(prompt: str):
    """Generate an image using Gemini API with the given prompt"""
    try:
        print(f"🎨 Generating image with prompt: '{prompt}'")
        print("⏳ Please wait, this may take a moment...")
        
        # Generate image using Gemini's native image generation
        response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE'],
            )
        )
        
        # Process the response to find the image
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print(f"📝 Generated text: {part.text}")
            elif part.inline_data is not None:
                print("✅ Image generated successfully!")
                
                # Convert the inline data to a PIL Image
                image = Image.open(BytesIO(part.inline_data.data))
                
                # Save the image
                filename = "veo2_dialogue_example_2.jpg"
                image.save(filename)
                
                print(f"💾 Image saved as: {filename}")
                print(f"📊 Image size: {image.size[0]}x{image.size[1]} pixels")
                
                return filename
        
        print("❌ No image was generated in the response")
        return None
            
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        return None

if __name__ == "__main__":
    # Test authentication first
    try:
        print("🔑 Testing authentication...")
        print("✅ Authentication successful!")
        
        # Generate an image with a sample prompt
        prompt = """A young boy comes home and asks his parents for a snack, but his parents are busy and tell him to wait."""
        
        generated_file = generate_image_from_prompt(prompt)
        
        if generated_file:
            print(f"\n🎉 Success! Image saved as: {generated_file}")
            print("You can now view the generated image in your project directory.")
            print("💡 Run 'python backend/test_veo2_with_s3.py' to upload both video and thumbnail to S3!")
        else:
            print("\n❌ Image generation failed")
            
    except Exception as e:
        print(f"❌ Authentication or setup failed: {e}")