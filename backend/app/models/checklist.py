# backend/app/models/checklist.py
from pydantic import BaseModel
from typing import List, Dict, Any

class Section(BaseModel):
    component: str
    props: Dict[str, Any]

class Page(BaseModel):
    name: str
    path: str
    sections: List[Section]

class Branding(BaseModel):
    colors: Dict[str, str]

class Checklist(BaseModel):
    branding: Branding
    pages: List[Page]

class GenerateRequest(BaseModel):
    checklist: Checklist