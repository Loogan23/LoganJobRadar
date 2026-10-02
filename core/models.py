from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    city: Optional[str] = ""
    state: Optional[str] = ""
    is_remote: bool = False
    modality: str = "Presencial" # Remoto, Híbrido, Presencial
    url: str
    source: str # LinkedIn, Gupy, etc.
    description: Optional[str] = ""
    seniority: Optional[str] = ""
    track_matched: Optional[str] = ""
    match_score: float = 0.0
    score_reasons: List[str] = Field(default_factory=list)
    published_at: Optional[str] = ""
    raw_data: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ScoreResult(BaseModel):
    is_eligible: bool = True
    disqualification_reason: Optional[str] = None
    total_score: float = 0.0
    title_score: float = 0.0
    keywords_score: float = 0.0
    location_score: float = 0.0
    seniority_score: float = 0.0
    matched_track: str = ""
    matched_keywords: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)

class ScrapingSummary(BaseModel):
    total_found: int = 0
    total_eligible: int = 0
    total_high_match: int = 0
    sources_scraped: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
