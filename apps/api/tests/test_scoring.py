from app.domain.scoring import combine_scores, score_features

def test_explainable_feature_contributions():
    result=score_features(["owner_filing","exact_full_name","same_city"])
    assert result.score==52
    assert result.contributions[0]=={"feature":"owner_filing","impact":25}

def test_overall_uses_weaker_proposition_not_average():
    assert combine_scores(95,35)==35
    assert combine_scores(90,85)==90
    assert combine_scores(90,85,20)==70

def test_registered_agent_is_negative_identity_evidence():
    assert score_features(["exact_full_name","same_city","registered_agent_only"]).score==0
