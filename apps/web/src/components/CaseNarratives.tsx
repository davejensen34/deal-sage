import {AlertTriangle, CheckCircle2, Search} from 'lucide-react';

export type CaseNarrative={
  id:number;origin_strategy:string;status:string;stop_reason:string|null;
  hypothesis:{direction:string;subject:string;candidate:string;status:string}|null;
  confidence:{business_identity:number;owner_relationship:number;transition_identity:number;operating_status:number;overall_opportunity:number;method_version:string;factors:unknown[]}|null;
  searches:{query:string;provider:string;status:string;result_count:number}[];
  evidence:{publisher:string;source_type:string;canonical_url:string;classification:string;relevant_excerpt:string|null}[];
  conflicts:{type:string;rationale:string;status:string}[];
  frontier:{question:string;rationale:string;priority:number;status:string}[];
  steps:{number:number;action:string;provider:string|null;model:string|null;status:string;cost_cents:number}[];
  conclusion:{analyst:string;outcome:string;statement:string;status:string}|null;
};

const label=(value:string)=>value.replaceAll('_',' ');

export function CaseNarratives({cases}:{cases:CaseNarrative[]}){
  return <section className="panel case-narratives">
    <div className="panel-title"><div><p className="eyebrow">Evidence convergence</p><h2>Research cases</h2><p>Origin, searches, evidence, conflicts, confidence, stopping, and human judgment remain traceable.</p></div><span>{cases.length} cases</span></div>
    {cases.length===0?<div className="case-empty"><Search/><div><b>No convergence cases yet</b><p>Cases will appear here when bounded signal-first, business-first, or hybrid research begins.</p></div></div>:
      <div className="case-list">{cases.map(item=><details key={item.id}>
        <summary><span>Case {item.id}</span><b>{label(item.origin_strategy)}</b><small>{label(item.stop_reason||item.status)}</small>{item.confidence&&<strong>{item.confidence.overall_opportunity}% opportunity</strong>}</summary>
        <div className="case-body">
          {item.hypothesis&&<p><b>Hypothesis:</b> {item.hypothesis.subject} → {item.hypothesis.candidate} ({label(item.hypothesis.direction)})</p>}
          {item.confidence&&<div className="case-scores">{[['Business identity',item.confidence.business_identity],['Owner relationship',item.confidence.owner_relationship],['Transition identity',item.confidence.transition_identity],['Operating status',item.confidence.operating_status]].map(([name,value])=><span key={name as string}><small>{name}</small><b>{value}%</b></span>)}</div>}
          <p><b>Research activity:</b> {item.searches.length} searches · {item.evidence.length} evidence items · {item.steps.length} bounded steps · {item.frontier.length} frontier questions</p>
          {item.conflicts.map((conflict,index)=><p className="case-conflict" key={`${conflict.type}-${index}`}><AlertTriangle/>{conflict.rationale}</p>)}
          {item.conclusion?<div className="case-conclusion"><CheckCircle2/><div><b>Analyst · {label(item.conclusion.outcome)}</b><p>{item.conclusion.statement}</p><small>{item.conclusion.analyst} · {item.conclusion.status}</small></div></div>:<p className="muted">No analyst conclusion recorded. A DealSage score is not a human decision.</p>}
        </div>
      </details>)}</div>}
  </section>;
}
