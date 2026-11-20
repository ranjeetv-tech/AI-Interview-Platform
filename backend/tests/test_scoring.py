from app.services.scoring import score_interview, classification

def test_weighted_score_is_deterministic():
    item={"category":"Technical","answer":"A detailed technical answer", "feedback":{"correctness":80,"relevance":90,"clarity":80,"depth":70,"completeness":75}}
    cats, overall=score_interview([item])
    assert 0 <= overall <= 100
    assert cats["Technical"] > 0

def test_classification():
    assert classification(45)=="Needs Improvement"
    assert classification(70)=="Good"
    assert classification(90)=="Interview Ready"
