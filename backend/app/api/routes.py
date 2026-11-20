from datetime import datetime
from pathlib import Path
import os
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.session import get_db
from app.models import Candidate, Resume, Interview, InterviewQuestion, InterviewAnswer, InterviewFeedback
from app.schemas.schemas import ResumeProfile, InterviewCreate, AnswerCreate
from app.services.ai_service import analyze_resume, analyze_jd, next_question, analyze_answer, follow_up, final_feedback
from app.services.scoring import score_interview, classification
from app.services.demo import DEMO_PROFILE
from app.utils.files import ALLOWED, safe_filename, extract_text

router = APIRouter(prefix="/api")

def serialize_question(q):
    return {"id":q.id,"question_number":q.question_number,"question":q.question,"category":q.category,"topic":q.topic,"difficulty":q.difficulty}

def interview_dict(i):
    return {"id":i.id,"date":(i.completed_at or i.started_at or datetime.utcnow()).isoformat(),"role":i.role,"type":i.interview_type,"difficulty":i.difficulty,"duration":i.duration_minutes,"score":i.overall_score,"status":i.status}

@router.get("/health")
def health(): return {"status":"ok","app":"InterviewAI"}

@router.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED: raise HTTPException(400, "Only PDF and DOCX resumes are supported.")
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024: raise HTTPException(413, "Resume exceeds the upload size limit.")
    os.makedirs(settings.upload_dir, exist_ok=True)
    path = os.path.join(settings.upload_dir, safe_filename(file.filename))
    with open(path, "wb") as f: f.write(data)
    try: text = extract_text(path)
    except Exception as e: raise HTTPException(422, f"Could not read the resume: {e}")
    if not text.strip(): raise HTTPException(422, "The resume contains no extractable text.")
    try: profile = await analyze_resume(text)
    except Exception as e: raise HTTPException(502, f"Resume AI analysis failed: {e}")
    candidate = Candidate(name=profile.get("name") or "Candidate")
    resume = Resume(candidate=candidate, original_filename=file.filename, extracted_text=text, structured_profile=profile)
    db.add(resume); db.commit(); db.refresh(resume); db.refresh(candidate)
    return {"candidate_id":candidate.id,"resume_id":resume.id,"profile":profile}

@router.post("/resume/demo")
def demo_resume(db: Session = Depends(get_db)):
    candidate = Candidate(name=DEMO_PROFILE["name"])
    resume = Resume(candidate=candidate, original_filename="demo-profile.json", extracted_text="Demo profile supplied by InterviewAI.", structured_profile=DEMO_PROFILE)
    db.add(resume); db.commit(); db.refresh(resume); db.refresh(candidate)
    return {"candidate_id":candidate.id,"resume_id":resume.id,"profile":DEMO_PROFILE,"demo":True}

@router.post("/interviews")
async def create_interview(payload: InterviewCreate, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, payload.candidate_id)
    if not candidate: raise HTTPException(404, "Candidate not found")
    jd_analysis = payload.jd_analysis.model_dump() if payload.jd_analysis else {}
    if payload.job_description and not jd_analysis:
        try: jd_analysis = await analyze_jd(payload.job_description)
        except Exception as e: raise HTTPException(502, f"JD analysis failed: {e}")
    i = Interview(candidate_id=payload.candidate_id, role=payload.role, interview_type=payload.interview_type, difficulty=payload.difficulty, duration_minutes=payload.duration_minutes, job_description=payload.job_description, jd_analysis=jd_analysis, config_json=payload.model_dump())
    db.add(i); db.commit(); db.refresh(i)
    return interview_dict(i)

@router.get("/interviews")
def list_interviews(db: Session = Depends(get_db)):
    return [interview_dict(i) for i in db.query(Interview).order_by(Interview.id.desc()).all()]

@router.get("/interviews/{iid}")
def get_interview(iid:int, db:Session=Depends(get_db)):
    i=db.get(Interview,iid)
    if not i: raise HTTPException(404,"Interview not found")
    questions=[]
    for q in i.questions:
        item=serialize_question(q)
        if q.answer: item["answer"]={"transcript":q.answer.transcript,"score":q.answer.question_score,"feedback":q.answer.feedback.__dict__ if q.answer.feedback else None}
        questions.append(item)
    return {**interview_dict(i),"candidate":i.candidate.name,"questions":questions}

@router.post("/interviews/{iid}/start")
async def start_interview(iid:int, db:Session=Depends(get_db)):
    i=db.get(Interview,iid)
    if not i: raise HTTPException(404,"Interview not found")
    if i.status == "SETUP":
        i.status="INITIALIZING"; i.started_at=datetime.utcnow(); db.commit()
    if not i.questions:
        resume = i.candidate.resumes[-1] if i.candidate.resumes else None
        profile = resume.structured_profile if resume else DEMO_PROFILE
        qd = await next_question(profile,i.role,i.interview_type,i.difficulty,i.job_description,[])
        q=InterviewQuestion(interview_id=i.id,question_number=1,question=qd["question"],category=qd["category"],topic=qd.get("topic",""),difficulty=qd.get("difficulty",i.difficulty))
        db.add(q); i.status="AI_SPEAKING"; db.commit(); db.refresh(q)
    return {"interview":interview_dict(i),"question":serialize_question(i.questions[0] if i.questions else q)}

@router.post("/interviews/{iid}/answer")
async def submit_answer(iid:int,payload:AnswerCreate,db:Session=Depends(get_db)):
    i=db.get(Interview,iid)
    if not i: raise HTTPException(404,"Interview not found")
    q=db.get(InterviewQuestion,payload.question_id)
    if not q or q.interview_id != iid: raise HTTPException(404,"Question not found")
    if q.answer: raise HTTPException(409,"This question already has an answer")
    try: analysis=await analyze_answer(q.question,q.category,payload.transcript)
    except Exception as e: raise HTTPException(502,f"Answer analysis failed: {e}")
    a=InterviewAnswer(question_id=q.id,transcript=payload.transcript,audio_seconds=payload.audio_seconds,claims=analysis.get("claims",[]),missing_concepts=analysis.get("missing_concepts",[]),question_score=float(analysis.get("score",0)))
    fb=InterviewFeedback(answer=a,correctness=float(analysis.get("correctness",0)),relevance=float(analysis.get("relevance",0)),clarity=float(analysis.get("clarity",0)),depth=float(analysis.get("depth",0)),completeness=float(analysis.get("completeness",0)),strengths=analysis.get("strengths",[]),missing_points=analysis.get("missing_points",[]),issues=analysis.get("issues",[]),follow_up_required=1 if analysis.get("follow_up_required") else 0,follow_up_reason=analysis.get("follow_up_reason", ""))
    db.add(a); db.add(fb); i.status="FOLLOW_UP_DECISION"; db.commit(); db.refresh(a)
    return {"analysis":analysis,"question_id":q.id}

@router.post("/interviews/{iid}/next-question")
async def get_next_question(iid:int,db:Session=Depends(get_db)):
    i=db.get(Interview,iid)
    if not i: raise HTTPException(404,"Interview not found")
    memory=[]
    for q in i.questions:
        memory.append({"question":q.question,"category":q.category,"topic":q.topic,"answer":q.answer.transcript if q.answer else "","score":q.answer.question_score if q.answer else None,"missing":q.answer.missing_concepts if q.answer else []})
    last=i.questions[-1]
    if last.answer and last.answer.feedback and last.answer.feedback.follow_up_required:
        qd=await follow_up(last.question,last.answer.transcript,{"score":last.answer.question_score,"missing_concepts":last.answer.missing_concepts,"issues":last.answer.feedback.issues},memory)
    else:
        resume=i.candidate.resumes[-1] if i.candidate.resumes else None
        profile=resume.structured_profile if resume else DEMO_PROFILE
        qd=await next_question(profile,i.role,i.interview_type,i.difficulty,i.job_description,memory)
    q=InterviewQuestion(interview_id=i.id,question_number=len(i.questions)+1,question=qd["question"],category=qd["category"],topic=qd.get("topic",""),difficulty=qd.get("difficulty",i.difficulty),follow_up_to_id=last.id if last.answer and last.answer.feedback and last.answer.feedback.follow_up_required else None)
    db.add(q); i.status="AI_SPEAKING"; db.commit(); db.refresh(q)
    return serialize_question(q)

@router.post("/interviews/{iid}/complete")
async def complete(iid:int,db:Session=Depends(get_db)):
    i=db.get(Interview,iid)
    if not i: raise HTTPException(404,"Interview not found")
    answers=[{"question":q.question,"category":q.category,"answer":q.answer.transcript,"feedback":q.answer.feedback.__dict__ if q.answer.feedback else {},"score":q.answer.question_score} for q in i.questions if q.answer]
    cats,overall=score_interview(answers)
    try: final=await final_feedback(i.config_json,answers)
    except Exception: final={"summary":"AI final feedback was unavailable; the deterministic score is still shown.","strengths":[],"weaknesses":[],"fix_this_first":{},"study_plan":{"revise":[],"practice":[],"communication":[]},"category_evidence":{}}
    i.status="REPORT"; i.completed_at=datetime.utcnow(); i.category_scores=cats; i.overall_score=overall; i.final_feedback=final; db.commit(); db.refresh(i)
    return {"id":i.id,"score":overall,"classification":classification(overall),"category_scores":cats,"feedback":final}

@router.get("/interviews/{iid}/feedback")
def feedback(iid:int,db:Session=Depends(get_db)):
    i=db.get(Interview,iid)
    if not i: raise HTTPException(404,"Interview not found")
    return {"id":i.id,"score":i.overall_score,"classification":classification(i.overall_score or 0),"category_scores":i.category_scores or {},"feedback":i.final_feedback or {}}

@router.delete("/interviews/{iid}")
def delete_interview(iid:int,db:Session=Depends(get_db)):
    i=db.get(Interview,iid)
    if not i: raise HTTPException(404,"Interview not found")
    db.delete(i); db.commit(); return {"deleted":True}

@router.get("/dashboard")
def dashboard(db:Session=Depends(get_db)):
    completed=db.query(Interview).filter(Interview.status=="REPORT").all()
    scores=[i.overall_score for i in completed if i.overall_score is not None]
    return {"interviews_completed":len(completed),"average_score":round(sum(scores)/len(scores),1) if scores else 0,"best_score":max(scores) if scores else 0,"latest_score":scores[0] if scores else 0,"total_practice_minutes":sum(i.duration_minutes for i in completed),"trend":[{"date":i.completed_at.isoformat() if i.completed_at else "","score":i.overall_score or 0,"technical":(i.category_scores or {}).get("Technical",0),"communication":(i.category_scores or {}).get("Communication",0),"projects":(i.category_scores or {}).get("Projects",0),"behavioral":(i.category_scores or {}).get("Behavioral",0)} for i in completed[-12:]]}
