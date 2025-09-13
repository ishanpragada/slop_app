from pydantic import BaseModel, Field
from typing import Optional

class PromptRequest(BaseModel):
    """Request model for prompt generation"""
    base_topic: Optional[str] = Field(None, description="Optional base topic to enhance")

class PromptResult(BaseModel):
    """Result of prompt generation"""
    prompt: str = Field(..., description="Detailed prompt for Veo 3 Fast generation")
    base_topic: str = Field(..., description="Original base topic used")
    style: str = Field(..., description="Visual style applied")
    camera_movement: str = Field(..., description="Camera movement technique")
    lighting: str = Field(..., description="Lighting style used")
    category: str = Field(..., description="Content category")
    generation_method: str = Field(..., description="Method used for generation") 