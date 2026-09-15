from app.services.research_cost_coverage import research_cost_coverage
from app.domain.models import ResearchQuery,AIExecution
from test_case_workflow_metrics import override_db_session
from test_case_decisions import setup

def test_empty_inventory_and_unpriced_usage_stay_unknown(override_db_session):
    db=override_db_session
    r=research_cost_coverage(db)
    assert r['grand_total'] is None and all(x['records']==0 for x in r['rows'])
    case,_,_=setup(db)
    db.add(ResearchQuery(case_id=case.id,query_text='Unpriced search',provider='openai_web_search',max_results=5,status='failed'))
    db.add(ResearchQuery(case_id=case.id,query_text='Fixture search',provider='fixture',max_results=5,status='succeeded'))
    db.add(AIExecution(provider='openai',model='historical',prompt_version='v1',input_tokens=10,output_tokens=5,success=True))
    db.commit();r=research_cost_coverage(db);rows={x['name']:x for x in r['rows']}
    assert rows['Search queries']['records']==2 and rows['Search queries']['missing_cost_records']==1
    assert rows['Search queries']['recorded_amount'] is None
    assert rows['Legacy candidate AI executions']['missing_cost_records']==1
    assert rows['Legacy candidate AI executions']['recorded_amount'] is None
    assert r['grand_total'] is None

def test_followup_step_reservation_not_added_to_legacy_ledger(override_db_session):
    from test_followups import make,execute
    db=override_db_session;case,run=make(db);execute(db,run)
    rows={x['name']:x for x in research_cost_coverage(db)['rows']}
    assert rows['Legacy research steps']['records']==0
