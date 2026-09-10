import {render,screen} from '@testing-library/react';
import {expect,it} from 'vitest';
import {WorkflowEffectiveness} from './WorkflowEffectiveness';

it('shows measured lineage and explicit unattributed candidates',()=>{
  render(<WorkflowEffectiveness result={{candidate_total:18,attributed_candidates:1,unattributed_candidates:17,attribution_coverage_percent:5.6,analyst_decisions:{validated:4,rejected:5},sources:[{source_key:'utah_bel',jurisdictions:['Utah'],acquisition_runs:2,refresh_runs:0,refresh_outcomes:{},unique_artifacts:4,curated_records:188,quarantined_records:0,recorded_refresh_cost_usd:0,freshness_outcomes:{},attributed_candidates:1,analyst_decisions:{validated:1},decision_reason_codes:{evidence_supported:1}}],measurement_boundaries:{attribution_basis:'research_case_evidence_to_raw_artifact_to_acquisition_run',durable_lineage_available:true,lineage_unavailable_reason:null,multi_source_candidate_counts_are_additive:false,unlinked_candidates_are_not_inferred:true,cost_scope:'source_refresh_records_only',raw_record_content_included:false}}}/>);
  expect(screen.getByText('1 / 18')).toBeInTheDocument();
  expect(screen.getByText('17')).toBeInTheDocument();
  expect(screen.getByText('No source is guessed')).toBeInTheDocument();
  expect(screen.getByText(/Cost covers source refresh records only/)).toBeInTheDocument();
  expect(screen.getByText('1 candidates')).toBeInTheDocument();
});
