from typing import Any
from pydantic import BaseModel, Field

class ResumeProfile(BaseModel):
    name: str = ""
    education: list[str] = []
    skills: list[str] = []
    projects: list[str] = []
    experience: list[str] = []
    certifications: list[str] = []
    achievements: list[str] = []

class JDAnalysis(BaseModel):
    role: str = ""
    responsibilities: list[str] = []
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    technologies: list[str] = []
    keywords: list[str] = []

class InterviewCreate(BaseModel):
    candidate_id: int
    resume_id: int | None = None
    role: str
    interview_type: str = "Mixed"
    difficulty: str = "Real Interview"
    duration_minutes: int = Field(20, ge=10, le=30)
    job_description: str = ""
    jd_analysis: JDAnalysis | None = None

class AnswerCreate(BaseModel):
    question_id: int
    transcript: str = Field(min_length=1, max_length=12000)
    audio_seconds: float = Field(0, ge=0, le=600)

class QuestionResponse(BaseModel):
    id: int
    question_number: int
    question: str
    category: str
    topic: str
    difficulty: str

class DashboardStats(BaseModel):
    interviews_completed: int
    average_score: float
    best_score: float
    latest_score: float
    total_practice_minutes: int
