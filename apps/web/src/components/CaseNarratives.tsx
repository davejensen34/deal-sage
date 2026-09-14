import {AlertTriangle, CheckCircle2, Search} from 'lucide-react';
import {ModelProposal,ProposalReview} from './ProposalReview';
import {DiscoveryLead,DiscoveryLeads} from './DiscoveryLeads';
import {TransitionReview,TransitionReviewItem} from './TransitionReview';
import {BusinessBrief,LeadBrief} from './BusinessBrief';

export type CaseNarrative={
  id:number;origin_strategy:string;status:string;stop_reason:string|null;
  hypothesis:{direction:string;subject:string;candidate:string;status:string}|null;
  confidence:{business_identity:number;owner_relationship:number;transition_identity:number;operating_status:number;overall_opportunity:number;method_version:string;factors:unknown[]}|null;
  searches:{query:string;provider:string;status:string;result_count:number}[];
  evidence:{id?:number;publisher:string;source_type:string;canonical_url:string;classification:string;relevant_excerpt:string|null}[];
  conflicts:{type:string;rationale:string;status:string}[];
  frontier:{question:string;rationale:string;priority:number;status:string}[];
  steps:{number:number;action:string;provider:string|null;model:string|null;status:string;cost_cents:number}[];
  conclusion:{analyst:string;outcome:string;statement:string;status:string}|null;
  model_proposals:ModelProposal[];
  discovery_leads?:DiscoveryLead[];
  transitions?:TransitionReviewItem[];
  lead_brief?:LeadBrief;
};

const label=(value:string)=>value.replaceAll('_',' ');

export function CaseNarratives({cases}:{cases:CaseNarrative[]}){
  return <section className="panel case-narratives">
    <div className="panel-title"><div><p className="eyebrow">Business and transition intelligence</p><h2>Business research briefs</h2><p>What changed, why it may matter, and the evidence behind each lead. Recent signals appear before undated leads and historical background.</p></div><span>{cases.length} cases</span></div>
    {cases.length===0?<div className="case-empty"><Search/><div><b>No convergence cases yet</b><p>Cases will appear here when bounded signal-first, business-first, or hybrid research begins.</p></div></div>:
      <div className="case-list">{[...cases].sort((a,b)=>(a.lead_brief?.order??1)-(b.lead_brief?.order??1)).map(item=><article className="brief-case" key={item.id}>
        {item.lead_brief&&<BusinessBrief brief={item.lead_brief} evidence={item.evidence}/>}
        {item.model_proposals.filter(p=>p.execution_outcome==='completed'&&typeof p.proposed_output?.summary==='string'&&p.dispositions.at(-1)?.decision!=='reject').slice(-1).map(p=><section className="brief-model" key={p.id}><h4>Model insight · {p.provider}</h4><p>{p.proposed_output!.summary as string}</p><small>Proposal #{p.id} · Evidence {p.supported_evidence_ids.map(id=>`#${id}`).join(', ')} · {p.created_at.slice(0,10)}. Original model interpretation · review: {p.dispositions.at(-1)?.decision||'pending'}. Not a source assertion or analyst decision; corrections remain in the review record.</small></section>)}
        <details className="case-review"><summary><span>Case {item.id} · Evidence, models and analyst review</span><b>{label(item.origin_strategy)}</b><small>{label(item.stop_reason||item.status)}</small>{item.confidence&&<strong>{item.confidence.overall_opportunity}% opportunity</strong>}</summary>
        <div className="case-body">
          {item.hypothesis&&<p><b>Hypothesis:</b> {item.hypothesis.subject} → {item.hypothesis.candidate} ({label(item.hypothesis.direction)})</p>}
          {item.confidence&&<div className="case-scores">{[['Business identity',item.confidence.business_identity],['Owner relationship',item.confidence.owner_relationship],['Transition identity',item.confidence.transition_identity],['Operating status',item.confidence.operating_status]].map(([name,value])=><span key={name as string}><small>{name}</small><b>{value}%</b></span>)}</div>}
          <p><b>Research activity:</b> {item.searches.length} searches · {item.evidence.length} evidence items · {item.steps.length} bounded steps · {item.frontier.length} frontier questions</p>
          {!!item.discovery_leads?.length&&<DiscoveryLeads caseId={item.id} open={item.status==='open'} leads={item.discovery_leads}/>}
          <TransitionReview items={item.transitions||[]}/>
          {item.frontier.length>0&&<section><h3>Follow-up questions</h3>{item.frontier.map((question,index)=><p key={index}><b>{question.question}</b> · priority {question.priority} · {label(question.status)}<br/>{question.rationale}</p>)}</section>}
          {item.conflicts.map((conflict,index)=><p className="case-conflict" key={`${conflict.type}-${index}`}><AlertTriangle/>{conflict.rationale}</p>)}
          {item.model_proposals.length>0&&<div className="proposal-list"><h3>Model proposals requiring human judgment</h3>{item.model_proposals.map(proposal=><ProposalReview proposal={proposal} key={proposal.id}/>)}</div>}
          {item.conclusion?<div className="case-conclusion"><CheckCircle2/><div><b>Analyst · {label(item.conclusion.outcome)}</b><p>{item.conclusion.statement}</p><small>{item.conclusion.analyst} · {item.conclusion.status}</small></div></div>:<p className="muted">No analyst conclusion recorded. A DealSage score is not a human decision.</p>}
        </div>
      </details></article>)}</div>}
  </section>;
}
