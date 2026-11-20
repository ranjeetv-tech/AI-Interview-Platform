from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), default="Demo Candidate")
    created_at = Column(DateTime, default=datetime.utcnow)
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="candidate", cascade="all, delete-orphan")

class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    extracted_text = Column(Text, nullable=False)
    structured_profile = Column(JSON, nullable=False)
    candidate = relationship("Candidate", back_populates="resumes")

class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    role = Column(String(150), nullable=False)
    interview_type = Column(String(50), nullable=False)
    difficulty = Column(String(50), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    job_description = Column(Text, default="")
    jd_analysis = Column(JSON, default=dict)
    config_json = Column(JSON, default=dict)
    status = Column(String(30), default="SETUP")
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    overall_score = Column(Float)
    category_scores = Column(JSON, default=dict)
    final_feedback = Column(JSON, default=dict)
    candidate = relationship("Candidate", back_populates="interviews")
    questions = relationship("InterviewQuestion", back_populates="interview", cascade="all, delete-orphan")

class InterviewQuestion(Base):
    __tablename__ = "interview_questions"
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    topic = Column(String(150), default="")
    difficulty = Column(String(50), default="Real Interview")
    follow_up_to_id = Column(Integer, ForeignKey("interview_questions.id"))
    interview = relationship("Interview", back_populates="questions")
    answer = relationship("InterviewAnswer", back_populates="question", uselist=False, cascade="all, delete-orphan")

class InterviewAnswer(Base):
    __tablename__ = "interview_answers"
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("interview_questions.id"), nullable=False, unique=True)
    transcript = Column(Text, nullable=False)
    audio_seconds = Column(Float, default=0)
    claims = Column(JSON, default=list)
    missing_concepts = Column(JSON, default=list)
    question_score = Column(Float)
    feedback = relationship("InterviewFeedback", back_populates="answer", uselist=False, cascade="all, delete-orphan")
    question = relationship("InterviewQuestion", back_populates="answer")

class InterviewFeedback(Base):
    __tablename__ = "interview_feedback"
    id = Column(Integer, primary_key=True)
    answer_id = Column(Integer, ForeignKey("interview_answers.id"), nullable=False, unique=True)
    correctness = Column(Float, default=0)
    relevance = Column(Float, default=0)
    clarity = Column(Float, default=0)
    depth = Column(Float, default=0)
    completeness = Column(Float, default=0)
    strengths = Column(JSON, default=list)
    missing_points = Column(JSON, default=list)
    issues = Column(JSON, default=list)
    follow_up_required = Column(Integer, default=0)
    follow_up_reason = Column(Text, default="")
    answer = relationship("InterviewAnswer", back_populates="feedback")
