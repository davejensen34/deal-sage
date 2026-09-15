import {useRef,useState} from 'react';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {api} from '../api/client';
import {useIdentity} from './AuthGate';
import {BusinessBrief,type LeadBrief} from './BusinessBrief';

type Changes=Record<string,{added:number[];removed:number[];changed:number[]}>;
type Content={case_status:string;source_brief:LeadBrief;sources:{id:number;publisher:string;canonical_url:string;relevant_excerpt:string;content_hash:string;excerpt_truncated:boolean}[];
  model_scope:{included:number;other_proposals:number};model_observations:{id:number;evidence_id:number;provider:string;model:string;review_state:string;review_id:number|null;source_changed:boolean;observations:{field:string;value:string;quote:string;certainty:string}[];unresolved_questions:string[]}[];
  reviews:{id:number;proposal_id:number;analyst:string;decision:string;rationale:string;corrected_output:unknown}[];
  conclusions:{id:number;analyst:string;outcome:string;statement:string;status:string}[];
  questions:{id:number;question:string;rationale:string;status:string;priority:number}[];transitions:unknown[]};
type Preview={content:Content;content_hash:string;latest_version:number;unchanged:boolean;changes:Changes};
type Version={version:number;actor:string;created_at:string;content_hash:string;content:Content;changes:Changes};
const words=(s:string)=>s.replaceAll('_',' ');
function Delta({changes}:{changes:Changes}){return <section><h4>Records changed since the previous saved version</h4><p>These are changes to retained records, not proof of a real-world event.</p>{Object.entries(changes).map(([group,change])=><p key={group}>{words(group)}: {change.added.length} added · {change.changed.length} changed · {change.removed.length} removed</p>)}</section>}
function BriefContent({content}:{content:Content}){return <>
  <h3>Source-backed research brief</h3><BusinessBrief brief={content.source_brief} evidence={content.sources}/>
  <h3>Model observations · separate from source facts</h3><p>{content.model_scope.included} quoted extraction proposals included. {content.model_scope.other_proposals} other or unsuccessful proposals remain in case research history.</p>
  {content.model_observations.map(p=><article className="investigation-item" key={p.id}><h4>Proposal {p.id} · evidence {p.evidence_id} · {words(p.review_state)}</h4><p>{p.provider} / {p.model}. Original model interpretation; review corrections are shown separately below.</p>{p.source_changed&&<p>Source text or hash has changed since extraction. This retains the earlier quoted observation.</p>}
    {!p.observations.length&&<p>No supported observations extracted.</p>}{p.observations.map((o,i)=><div key={i}><p><b>{words(o.field)}: {o.value}</b> · {words(o.certainty)}</p><blockquote>{o.quote}</blockquote><p>Model-cited evidence {p.evidence_id}; quotation matching does not verify field meaning.</p></div>)}
    {p.unresolved_questions.map((q,i)=><p key={i}>Model question: {q}</p>)}
  </article>)}
  <h3>Human review records</h3><p>Saving a brief records this view. It does not accept model output or create an analyst conclusion.</p>
  {!content.reviews.length&&!content.conclusions.length&&<p>No human judgments recorded.</p>}
  {content.reviews.map(r=><article key={`r${r.id}`}><h4>Review {r.id} · proposal {r.proposal_id} · {words(r.decision)}</h4><p>{r.analyst}: {r.rationale}</p>{r.corrected_output!==null&&<details><summary>Human-authored correction</summary><pre>{JSON.stringify(r.corrected_output,null,2)}</pre></details>}</article>)}
  {content.conclusions.map(c=><article key={`c${c.id}`}><h4>Conclusion {c.id} · {words(c.outcome)} · {c.status}</h4><p>{c.analyst}: {c.statement}</p></article>)}
  <h3>Follow-up questions</h3>{!content.questions.length&&<p>No frontier questions recorded. The source brief and model questions above retain remaining gaps.</p>}{content.questions.map(q=><p key={q.id}><b>{q.question}</b> · {words(q.status)}<br/>{q.rationale}</p>)}
  <details><summary>All retained transition assertions ({content.transitions.length})</summary><pre>{JSON.stringify(content.transitions,null,2)}</pre></details>
  <details><summary>Frozen source references ({content.sources.length})</summary>{content.sources.map(s=><article key={s.id}><h4>Evidence {s.id} · {s.publisher}</h4><blockquote>{s.relevant_excerpt||'No excerpt retained.'}</blockquote>{s.excerpt_truncated&&<p>Display excerpt limited to 2,000 characters.</p>}<p>SHA-256 <code>{s.content_hash}</code></p></article>)}</details>
</>}

export function CaseBriefVersions({caseId}:{caseId:number}){
  const [open,setOpen]=useState(false),[page,setPage]=useState(1),[selected,setSelected]=useState<number|null>(null),[prepared,setPrepared]=useState<Preview|null>(null);
  const key=useRef<string|null>(null),identity=useIdentity(),qc=useQueryClient();
  const preview=useMutation({mutationFn:()=>api<Preview>(`/research/cases/${caseId}/brief-preview`),onSuccess:p=>{setPrepared(p);setSelected(null);key.current=null}});
  const history=useQuery({queryKey:['brief-versions',caseId,page],queryFn:()=>api<{items:Version[];has_next:boolean}>(`/research/cases/${caseId}/brief-versions?page=${page}`),enabled:open});
  const detail=useQuery({queryKey:['brief-version',caseId,selected],queryFn:()=>api<Version>(`/research/cases/${caseId}/brief-versions/${selected}`),enabled:selected!==null});
  const save=useMutation({mutationFn:()=>{key.current ||= crypto.randomUUID();return api<Version>(`/research/cases/${caseId}/brief-versions`,{method:'POST',body:JSON.stringify({request_key:key.current,expected_hash:prepared?.content_hash,expected_version:prepared?.latest_version})})},onSuccess:v=>{setSelected(v.version);setPrepared(null);key.current=null;qc.invalidateQueries({queryKey:['brief-versions',caseId]})}});
  return <section className="panel case-investigation"><h2>Case brief versions</h2><p>Save an attributable view of source reports, cited model observations and human judgments. Later evidence changes cannot rewrite an earlier version.</p>
    <button aria-expanded={open} onClick={()=>setOpen(!open)}>{open?'Hide':'Open'} brief versions</button>{open&&<>
      <button disabled={preview.isPending||save.isPending} onClick={()=>preview.mutate()}>Preview current case brief</button>
      {preview.error&&<p role="alert">{preview.error.message}</p>}
      {prepared&&<div><h3>Current preview · after version {prepared.latest_version}</h3><p>{prepared.unchanged?'No included inputs changed since the latest saved version.':'New or changed included inputs are available to save.'}</p><p>No source or model calls. No new judgment or score change.</p>
        <button disabled={identity?.role==='viewer'||!identity||prepared.unchanged||save.isPending} onClick={()=>save.mutate()}>{save.isPending?'Saving…':key.current?'Retry same brief save':'Save this brief version'}</button>
        <Delta changes={prepared.changes}/><BriefContent content={prepared.content}/>
      </div>}
      {save.error&&<p role="alert">{save.error.message}</p>}
      <h3>Saved versions</h3>{history.isError?<p role="alert">Version history unavailable. <button onClick={()=>history.refetch()}>Try again</button></p>:history.isLoading?<p>Loading versions…</p>:<>
        {!history.data?.items.length&&<p>No saved brief versions yet.</p>}{history.data?.items.map(v=><p key={v.version}><button onClick={()=>{setPrepared(null);setSelected(v.version)}}>Open version {v.version}</button> · {v.actor} · {new Date(v.created_at).toLocaleString()}</p>)}
        <nav aria-label="Brief version pages"><button disabled={page===1} onClick={()=>setPage(page-1)}>Previous versions</button><span>Page {page}</span><button disabled={!history.data?.has_next} onClick={()=>setPage(page+1)}>Next versions</button></nav>
      </>}
      {selected!==null&&(detail.isLoading?<p>Loading saved version…</p>:detail.isError?<p role="alert">Saved version unavailable. <button onClick={()=>detail.refetch()}>Retry saved version</button></p>:detail.data&&<div><h3>Saved version {detail.data.version}</h3><p>Recorded by {detail.data.actor} · {new Date(detail.data.created_at).toLocaleString()}. Preview current inputs to check for newer information.</p><Delta changes={detail.data.changes}/><BriefContent content={detail.data.content}/></div>)}
    </>}
  </section>;
}
