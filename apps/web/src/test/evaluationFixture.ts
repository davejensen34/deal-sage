import type {ReviewPackage} from '../evaluationReview';
export const evaluationFixture:ReviewPackage={version:'m7-analyst-review-package-v1',result_sha256:'a'.repeat(64),bundle_sha256:'b'.repeat(64),items:[{
  slot:'FICTIONAL-CO-1',signal_type:'succession',requested_state:'CO',as_of:'2026-09-11',model:'fictional-model',
  sources:[{source_id:'1',url:'javascript:alert(1)',text:'Fictional source: <img src=x onerror=alert(1)>\nA leadership succession was announced in 2024.'}],
  summary:'Fictional Alpine Works announced management succession. Executive ownership remains unestablished.',
  questions:['Did the planned transition occur?','Who holds controlling ownership?'],contradictions:[],supported_source_ids:['1'],
  model_dimensions:{relationship:'non_owner_role',operating_status:'active',state_fit:'out_of_scope'},
  assessment:{version:'m7-observation-context-v1',temporal_scope:'historical',operating_status_at_assessment:'unknown',requested_state_operating_fit:'unknown',deterministic_research_disposition:'no_qualifying_relationship'},
  review_context:{reviewer:'Fictional review agent',review_kind:'agent_interpretation',operating_supported_on:'2024-06-03',operating_source_ids:['1'],geography_basis:'address',geography_state:'NC',geography_source_ids:['1']}
}]};
