from typing import List, Optional
from pydantic import BaseModel, Field

class Character(BaseModel):
    name: str
    description: str
    role: str = "supporting"
    visual_identity: str = ""

class Story(BaseModel):
    title: str
    logline: str
    genre: str
    tone: str
    characters: List[Character]
    panels: List[str]

class GenerateStoryRequest(BaseModel):
    premise: str = Field(min_length=3, max_length=4000)
    character_name: Optional[str] = None
    setting: Optional[str] = None
    language: str = "English"
    genre: str = "Adventure"
    tone: str = "Cinematic"
    panel_count: int = Field(default=5, ge=4, le=8)
    reference_image: Optional[str] = None

class RefineRequest(BaseModel):
    story: Story
    instruction: str = Field(min_length=2, max_length=2000)
    language: str = "English"

class StoryboardRequest(BaseModel):
    story: Story
    art_style: str = "Comic book"
    palette: str = "Rich cinematic colors"
    language: str = "English"

class GeneratePanelRequest(BaseModel):
    panel: dict
    story: Story
    art_style: str = "Comic book"
    palette: str = "Rich cinematic colors"
    aspect_ratio: str = "4:5"
    reference_image: Optional[str] = None
    premium: bool = False
    image_size: str = Field(default="1K", pattern=r"^(1K|2K|4K)$")

class UpscalePanelRequest(BaseModel):
    image: str
    panel: dict
    story: Story
    art_style: str = "Comic book"
    palette: str = "Rich cinematic colors"
    aspect_ratio: str = "4:5"
    image_size: str = Field(default="2K", pattern=r"^(2K|4K)$")

class ExportRequest(BaseModel):
    title: str = "ComicCraft Story"
    story: Story
    storyboard: dict
    images: List[dict] = []
