import json
from app.ai.provider import get_provider, parse_json
from app.prompts.prompts import *

async def ask(prompt: str, required_keys: list[str], retries: int = 1):
    provider = get_provider()
    last = None
    for _ in range(retries + 1):
        try:
            data = parse_json(await provider.complete(prompt))
            for key in required_keys:
                if key not in data:
                    raise ValueError(f"Missing key: {key}")
            return data
        except Exception as exc:
            last = exc
    raise RuntimeError(f"AI response validation failed: {last}")

async def analyze_resume(text: str):
    return await ask(RESUME_PROMPT.format(resume=text[:30000]), ["name","education","skills","projects","experience","certifications","achievements"])

async def analyze_jd(text: str):
    return await ask(JD_PROMPT.format(jd=text[:20000]), ["role","responsibilities","required_skills","preferred_skills","technologies","keywords"])

async def next_question(profile, role, itype, difficulty, jd, memory):
    return await ask(QUESTION_PROMPT.format(profile=json.dumps(profile), role=role, itype=itype, difficulty=difficulty, jd=jd[:12000], memory=json.dumps(memory)[-18000:]), ["question","category","topic","difficulty"])

async def analyze_answer(question, category, answer):
    return await ask(ANSWER_PROMPT.format(question=question, category=category, answer=answer[:12000]), ["score","correctness","relevance","clarity","depth","completeness","strengths","missing_points","issues","follow_up_required","follow_up_reason","claims","missing_concepts"])

async def follow_up(question, answer, analysis, previous):
    return await ask(FOLLOWUP_PROMPT.format(question=question, answer=answer[:10000], analysis=json.dumps(analysis),), ["question","category","topic","difficulty"])

async def final_feedback(config, answers):
    return await ask(FINAL_PROMPT.format(config=json.dumps(config), answers=json.dumps(answers)[-30000:]), ["summary","strengths","weaknesses","fix_this_first","study_plan","category_evidence"])
