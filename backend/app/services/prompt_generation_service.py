import os
import random
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types

class PromptGenerationService:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client()
        
        # Predefined categories for variety
        self.categories = [
            "comedy", "drama", "action", "romance", "horror", "sci-fi", 
            "fantasy", "documentary", "slice-of-life", "surreal", "artistic"
        ]
        
        # Visual style options
        self.visual_styles = [
            "cinematic", "documentary", "vintage", "modern", "artistic", 
            "commercial", "indie film", "blockbuster", "experimental", "minimalist"
        ]
        
        # Camera movements
        self.camera_movements = [
            "steady shot", "handheld", "dolly zoom", "panning", "tilting",
            "tracking shot", "aerial view", "low angle", "high angle", "close-up"
        ]
        
        # Lighting styles
        self.lighting_styles = [
            "natural daylight", "golden hour", "blue hour", "neon lights",
            "candlelight", "studio lighting", "moonlight", "street lights",
            "firelight", "fluorescent lighting"
        ]
    
    def generate_random_topic(self) -> str:
        """Generate a random funny/interesting topic using Gemini"""
        try:
            prompt = """
            Generate a single, creative, and engaging video concept that would be perfect for a short 8-second video. 
            Make it funny, interesting, or surprising. Focus on everyday situations with a twist.
            
            Requirements:
            - Should be something that can be visually interesting
            - Include a clear subject and action
            - Should be relatable or humorous
            - Keep it simple but engaging
            
            Return only the concept description, nothing else.
            """
            
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            
            return response.text.strip()
            
        except Exception as e:
            # Fallback to predefined topics if Gemini fails
            fallback_topics = [
                "A cat trying to open a door with its paw",
                "Someone discovering their phone is in their pocket after searching everywhere",
                "A person attempting to parallel park and failing spectacularly",
                "Someone trying to take a selfie with a group but everyone keeps moving",
                "A person cooking and accidentally adding salt instead of sugar",
                "Someone trying to fold a fitted sheet and getting frustrated",
                "A person trying to catch a bus but missing it by seconds",
                "Someone attempting to fix something with duct tape",
                "A person trying to remember a password and getting locked out",
                "Someone trying to take a photo of their food but the lighting is terrible"
            ]
            return random.choice(fallback_topics)
    
    def build_detailed_prompt(self, base_topic: str = None) -> str:
        """
        Build a detailed prompt for Veo 3 Fast video generation
        
        Args:
            base_topic: Optional base topic, if None will generate a random one
            
        Returns:
            Detailed prompt string optimized for Veo 3 Fast
        """
        try:
            # Generate or use provided topic
            if not base_topic:
                base_topic = self.generate_random_topic()
            
            # Build the detailed prompt using Gemini
            prompt_template = f"""
            Create a detailed, cinematic prompt for Veo 3 Fast video generation based on this concept: "{base_topic}"
            
            The prompt should include ALL of these elements:
            
            1. SUBJECT: Who or what is in the scene (be specific about appearance, clothing, age)
            2. CONTEXT: Where the scene takes place (specific location, environment)
            3. ACTION: What the subject is doing (detailed movement, gestures, expressions)
            4. STYLE: Visual aesthetic (choose from: {', '.join(self.visual_styles)})
            5. CAMERA: Camera movement and angle (choose from: {', '.join(self.camera_movements)})
            6. COMPOSITION: How the shot is framed (wide shot, medium shot, close-up, etc.)
            7. AMBIANCE: Mood and lighting (choose from: {', '.join(self.lighting_styles)})
            8. DETAILS: Small visual details that add character
            
            Important guidelines:
            - Make it cinematic and visually interesting
            - Include specific visual details
            - Create a clear mood or emotion
            - Make it engaging for 8 seconds
            - Focus on visual storytelling
            - Be specific about colors, textures, and lighting
            - Include subtle movements or actions
            
            Return only the detailed prompt, nothing else. Make it 2-3 sentences maximum.
            """
            
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt_template
            )
            
            detailed_prompt = response.text.strip()
            
            # Clean up the response
            if detailed_prompt.startswith('"') and detailed_prompt.endswith('"'):
                detailed_prompt = detailed_prompt[1:-1]
            
            return detailed_prompt
            
        except Exception as e:
            # Fallback to template-based generation
            return self._generate_fallback_prompt(base_topic)
    
    def _generate_fallback_prompt(self, base_topic: str) -> str:
        """Generate a detailed prompt using templates when Gemini fails"""
        style = random.choice(self.visual_styles)
        camera = random.choice(self.camera_movements)
        lighting = random.choice(self.lighting_styles)
        
        # Add cinematic details to the base topic
        enhanced_prompt = f"""
        A {style} shot with {camera} movement captures {base_topic.lower()}. 
        The scene is bathed in {lighting}, creating a warm and intimate atmosphere. 
        The composition focuses on the subject with shallow depth of field, 
        blurring the background into a dreamy bokeh effect.
        """
        
        return enhanced_prompt.strip()
    
    def generate_prompt_with_metadata(self, base_topic: str = None) -> Dict[str, Any]:
        """
        Generate a detailed prompt along with metadata for tracking
        
        Args:
            base_topic: Optional base topic
            
        Returns:
            Dictionary containing prompt and metadata
        """
        detailed_prompt = self.build_detailed_prompt(base_topic)
        
        return {
            "prompt": detailed_prompt,
            "base_topic": base_topic or "auto_generated",
            "style": random.choice(self.visual_styles),
            "camera_movement": random.choice(self.camera_movements),
            "lighting": random.choice(self.lighting_styles),
            "category": random.choice(self.categories),
            "generation_method": "gemini_enhanced"
        } 