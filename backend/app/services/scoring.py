WEIGHTS = {"Communication": .20, "Technical": .25, "Projects": .20, "Problem Solving": .15, "Behavioral": .10, "Delivery": .10}

def category_for(qcat: str):
    if qcat in {"Technical"}: return "Technical"
    if qcat in {"Projects", "Resume"}: return "Projects"
    if qcat in {"Behavioral"}: return "Behavioral"
    if qcat in {"Introduction", "Closing"}: return "Communication"
    return "Problem Solving"

def score_interview(items):
    buckets = {k: [] for k in WEIGHTS}
    for item in items:
        ev = item["feedback"]
        base = (float(ev.get("correctness", 0))*.35 + float(ev.get("relevance", 0))*.15 + float(ev.get("clarity", 0))*.15 + float(ev.get("depth", 0))*.20 + float(ev.get("completeness", 0))*.15)
        buckets[category_for(item["category"])].append(base)
        # delivery is derived only from observable transcript characteristics.
        text = item["answer"].lower()
        fillers = sum(text.count(x) for x in [" um ", " uh ", " like ", " you know "])
        delivery = max(0, min(100, 90 - fillers*4 - (10 if len(text.split()) < 8 else 0) - (8 if len(text.split()) > 450 else 0)))
        buckets["Delivery"].append(delivery)
    cats = {k: round(sum(v)/len(v), 1) if v else 0 for k,v in buckets.items()}
    overall = round(sum(cats[k]*w for k,w in WEIGHTS.items()), 1)
    return cats, overall

def classification(score):
    if score < 50: return "Needs Improvement"
    if score < 65: return "Developing"
    if score < 75: return "Good"
    if score < 88: return "Strong"
    return "Interview Ready"
