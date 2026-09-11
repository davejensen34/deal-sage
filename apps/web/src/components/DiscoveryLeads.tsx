import {useState} from 'react';
import {useQueryClient} from '@tanstack/react-query';
import {api} from '../api/client';
import {useIdentity} from './AuthGate';

export type DiscoveryLead={id:number;url:string;publisher:string;source_type:string;relevance:string;proposed_use:string;provider:string;query_ids:number[];discovery_queries?:string[];evidence_ids:number[];access:string;access_reason:string|null;priority:number;method:string;factors:{reason:string;points:number}[];next_action:string;question:string;frontier_id:number|null;frontier_status:string|null};

export function DiscoveryLeads({caseId,open,leads}:{caseId:number;open:boolean;leads:DiscoveryLead[]}){
  const client=useQueryClient();
  const identity=useIdentity();
  const [pending,setPending]=useState<number|null>(null);
  const [error,setError]=useState('');
  async function queue(id:number){
    setPending(id);setError('');
    try{
      await api(`/research/cases/${caseId}/discovery-leads/${id}/follow-up`,{method:'POST'});
      await client.invalidateQueries({queryKey:['research-case-narratives']});
    }catch(reason){setError(reason instanceof Error?reason.message:'Unable to queue follow-up');}
    finally{setPending(null);}
  }
  return <section className="discovery-leads">
    <h3>Discovery clues · {leads.length}</h3>
    <p>Unverified clues remain useful. Research priority orders investigation; it is not a probability, ownership score, or opportunity recommendation.</p>
    {!open&&<p className="muted">This case is stopped. Clues remain available for review; follow-ups will not restart it.</p>}
    {error&&<p role="alert">{error}</p>}
    {leads.map(lead=><article key={lead.id} className="discovery-lead">
      <div><b>{lead.publisher}</b><strong>Research priority {lead.priority}/100</strong></div>
      <p><a href={lead.url} target="_blank" rel="noreferrer">Inspect discovered source</a> · Provider-reported {lead.source_type.replaceAll('_',' ')}</p>
      <p><b>Search-provider suggestion, unverified:</b> {lead.relevance}</p>
      <p><b>Suggested use:</b> {lead.proposed_use.replaceAll('_',' ')}</p>
      {!!lead.discovery_queries?.length&&<details><summary>Discovery context</summary><ul>{lead.discovery_queries.map((query,index)=><li key={index}>{query}</li>)}</ul><p>Queries explain how this result surfaced; they do not establish a match.</p></details>}
      <p><b>Next question:</b> {lead.question}</p>
      <p><b>Access:</b> {lead.access} {lead.access_reason&&`· ${lead.access_reason}`}</p>
      <p><b>Evidence:</b> {lead.evidence_ids.length?`Retained items ${lead.evidence_ids.join(', ')}; not automatically accepted`:'Not yet retained; this is not a disproven claim'}</p>
      <details><summary>Why this priority?</summary><ul>{lead.factors.map((factor,index)=><li key={index}>+{factor.points}: {factor.reason}</li>)}</ul><small>{lead.method} · {lead.provider} · Queries {lead.query_ids.join(', ')||'not recorded'} · Repeated results add no weight.</small></details>
      <button disabled={!open||identity?.role==='viewer'||pending!==null||lead.frontier_id!==null} onClick={()=>queue(lead.id)}>{lead.frontier_id?`Follow-up ${lead.frontier_status?.replaceAll('_',' ')}`:pending===lead.id?'Queuing…':'Queue follow-up question'}</button>
    </article>)}
    <p className="muted">Queuing records a question for the bounded planner. It makes no external calls and does not accept a claim or approve source access.</p>
  </section>;
}
