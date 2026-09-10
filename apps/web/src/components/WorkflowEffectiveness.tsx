import {AlertTriangle,BarChart3,Link2,ShieldCheck} from 'lucide-react';

export type SourceEffectiveness={source_key:string;jurisdictions:string[];acquisition_runs:number;refresh_runs:number;refresh_outcomes:Record<string,number>;unique_artifacts:number;curated_records:number;quarantined_records:number;recorded_refresh_cost_usd:number;freshness_outcomes:Record<string,number>;latest_refresh_at?:string;attributed_candidates:number;analyst_decisions:Record<string,number>;decision_reason_codes:Record<string,number>};
export type WorkflowEffectivenessResult={candidate_total:number;attributed_candidates:number;unattributed_candidates:number;attribution_coverage_percent:number;analyst_decisions:Record<string,number>;sources:SourceEffectiveness[];measurement_boundaries:{attribution_basis:string;durable_lineage_available:boolean;lineage_unavailable_reason:string|null;multi_source_candidate_counts_are_additive:boolean;unlinked_candidates_are_not_inferred:boolean;cost_scope:string;raw_record_content_included:boolean}};

const label=(value:string)=>value.replaceAll('_',' ');
const summary=(values:Record<string,number>)=>Object.entries(values).map(([key,value])=>`${label(key)} ${value}`).join(' · ')||'none recorded';

export function WorkflowEffectiveness({result}:{result:WorkflowEffectivenessResult}){
  return <section className="panel workflow-effectiveness">
    <div className="panel-title"><div><p className="eyebrow">Milestone 5.1 · measured lineage</p><h2>Source-to-review effectiveness</h2><p>Only durable evidence lineage is attributed. Unlinked candidates remain explicitly unassigned.</p></div><BarChart3/></div>
    {!result.measurement_boundaries.durable_lineage_available&&<p className="measurement-warning"><AlertTriangle/> Candidate attribution is unavailable until the existing database applies the evidence-lineage migration. No source relationship has been inferred.</p>}
    <div className="effectiveness-summary">
      <div><Link2/><span>Attributed candidates</span><b>{result.attributed_candidates} / {result.candidate_total}</b><small>{result.attribution_coverage_percent}% coverage</small></div>
      <div><AlertTriangle/><span>Unattributed candidates</span><b>{result.unattributed_candidates}</b><small>No source is guessed</small></div>
      <div><ShieldCheck/><span>Analyst decisions</span><b>{Object.values(result.analyst_decisions).reduce((sum,value)=>sum+value,0)}</b><small>{summary(result.analyst_decisions)}</small></div>
    </div>
    <div className="effectiveness-table"><table><thead><tr><th>Source</th><th>Landing coverage</th><th>Freshness / cost</th><th>Candidate lineage</th><th>Analyst disposition</th></tr></thead><tbody>{result.sources.map(source=><tr key={source.source_key}><td><b>{label(source.source_key)}</b><span>{source.jurisdictions.join(', ')||'Jurisdiction unavailable'} · {source.acquisition_runs} acquisition runs</span></td><td>{source.curated_records} curated<small>{source.quarantined_records} quarantined · {source.unique_artifacts} artifacts</small></td><td>${source.recorded_refresh_cost_usd.toFixed(2)}<small>{summary(source.freshness_outcomes)}</small></td><td>{source.attributed_candidates} candidates<small>{source.attributed_candidates?'Durable case/artifact link':'No durable candidate link'}</small></td><td>{summary(source.analyst_decisions)}<small>{summary(source.decision_reason_codes)}</small></td></tr>)}</tbody></table></div>
    {!result.sources.length&&<p className="muted">No acquisition or refresh runs are recorded yet.</p>}
    <p className="measurement-note"><ShieldCheck/> Cost covers source refresh records only. Candidate totals across sources are not additive when one case uses multiple sources. Raw record content is excluded.</p>
  </section>
}
