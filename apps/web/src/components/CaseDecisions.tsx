import {useRef,useState} from 'react';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {api} from '../api/client';
import {useIdentity} from './AuthGate';
import '../pages/discovery.css';

type Decision={brief_version:number;expected_prior_id:number|null;outcome:string;purpose:string;rationale:string;next_action:string;supporting_source_ids:number[];contradicting_source_ids:number[];change_reason:string};
type Record={id:number;actor:string;created_at:string;prior_id:number|null;decision:Decision};
type Brief={version:number;actor:string;created_at:string;content:{source_brief:{title:string};sources:{id:number;publisher:string;relevant_excerpt:string}[]}};
const words=(s:string)=>s.replaceAll('_',' ');
function DecisionRecord({record}:{record:Record}){const d=record.decision;return <article className="investigation-item"><h4>{words(d.outcome)} · {words(d.purpose)}</h4><p>{record.actor} · {new Date(record.created_at).toLocaleString()} · brief version {d.brief_version} · decision {record.id}</p><p><b>Rationale:</b> {d.rationale}</p><p><b>Next action:</b> {d.next_action}</p><p>Supporting sources: {d.supporting_source_ids.join(', ')||'None selected'} · Contradicting sources: {d.contradicting_source_ids.join(', ')||'None selected'}</p>{record.prior_id&&<p>Replaces decision {record.prior_id}: {d.change_reason}</p>}</article>}

export function CaseDecisions({caseId}:{caseId:number}){
  const identity=useIdentity(),qc=useQueryClient();
  const [page,setPage]=useState(1),[version,setVersion]=useState(1),[brief,setBrief]=useState<Brief|null>(null),[prior,setPrior]=useState<number|null>(null);
  const [draft,setDraft]=useState({outcome:'more_research',purpose:'acquisition_exploration',rationale:'',next_action:'',change_reason:'',supporting_source_ids:[] as number[],contradicting_source_ids:[] as number[]});
  const pending=useRef<{request_key:string;decision:Decision}|null>(null);
  const history=useQuery({queryKey:['case-decisions',caseId,page],queryFn:()=>api<{items:Record[];has_next:boolean;latest:Record|null}>(`/research/cases/${caseId}/decisions?page=${page}`)});
  const load=useMutation({mutationFn:async()=>{const h=await history.refetch();if(h.error)throw h.error;const b=await api<Brief>(`/research/cases/${caseId}/brief-versions/${version}`);return {b,prior:h.data?.latest?.id??null}},onSuccess:({b,prior})=>{setBrief(b);setPrior(prior);pending.current=null;setDraft(d=>({...d,supporting_source_ids:[],contradicting_source_ids:[]}))}});
  const save=useMutation({mutationFn:()=>{pending.current ||= {request_key:crypto.randomUUID(),decision:{...draft,brief_version:brief!.version,expected_prior_id:prior}};return api<Record>(`/research/cases/${caseId}/decisions`,{method:'POST',body:JSON.stringify(pending.current)})},onSuccess:()=>{pending.current=null;setBrief(null);setDraft(d=>({...d,rationale:'',next_action:'',change_reason:''}));setPage(1);qc.invalidateQueries({queryKey:['case-decisions',caseId]})}});
  const edit=(value:Partial<typeof draft>)=>{pending.current=null;setDraft({...draft,...value})};
  const choose=(id:number,kind:'supporting_source_ids'|'contradicting_source_ids')=>{const other=kind==='supporting_source_ids'?'contradicting_source_ids':'supporting_source_ids';edit({[kind]:draft[kind].includes(id)?draft[kind].filter(v=>v!==id):[...draft[kind],id],[other]:draft[other].filter(v=>v!==id)})};
  const busy=save.isPending||load.isPending,canReview=!!identity&&identity.role!=='viewer';
  return <section className="panel case-investigation"><h2>Reviewer decision</h2><p>Record what should happen next for your purpose. This does not verify source claims, accept model output, change candidate status or start monitoring, research or communication.</p>
    {history.isError?<p role="alert">Decision history unavailable. <button onClick={()=>history.refetch()}>Reload decisions</button></p>:history.isLoading?<p>Loading decisions…</p>:history.data?.latest?<><h3>Current decision</h3><DecisionRecord record={history.data.latest}/></>:<p>No workflow decision recorded.</p>}
    {canReview&&<><h3>{history.data?.latest?'Record a replacement decision':'Record a decision'}</h3><p>First save and inspect a case brief in “Case brief versions.” Choose its exact version below; later source changes do not rewrite that reviewed record.</p>
      <form className="discovery-form" onSubmit={e=>{e.preventDefault();load.mutate()}}><label>Reviewed brief version<input type="number" min={1} required value={version} disabled={busy} onChange={e=>{setVersion(Number(e.target.value));setBrief(null);pending.current=null}}/></label><button disabled={busy||!history.data||history.isError}>Load reviewed brief</button></form>
      {brief&&<form className="discovery-form" onSubmit={e=>{e.preventDefault();save.mutate()}}><h3>Decision basis: version {brief.version} · {brief.content.source_brief.title}</h3><p>Saved by {brief.actor}. Source reports, original model observations and human judgments remain separately inspectable in the saved brief.</p>
        <label>Decision<select value={draft.outcome} disabled={busy} onChange={e=>edit({outcome:e.target.value})}><option value="more_research">More research</option><option value="monitor">Monitor</option><option value="dismiss">Dismiss</option></select></label>
        <label>Purpose<select value={draft.purpose} disabled={busy} onChange={e=>edit({purpose:e.target.value})}><option value="acquisition_exploration">Acquisition exploration</option><option value="marketing_introduction">Marketing introduction</option><option value="succession_advisory">Succession advisory</option></select></label>
        {(['rationale','next_action',...(prior?['change_reason']:[])] as ('rationale'|'next_action'|'change_reason')[]).map(name=><label key={name}>{name==='rationale'?'Decision rationale':name==='next_action'?'Next action':'Reason for changing the decision'}<input required minLength={10} maxLength={name==='rationale'?2000:1000} value={draft[name]} disabled={busy} onChange={e=>edit({[name]:e.target.value})}/></label>)}
        <h4>Source references from this saved version</h4><p>Selections express your reasoning, not verified source truth. Explain mixed evidence or the absence of support in the rationale.</p>
        {!brief.content.sources.length&&<p>No source references in this version.</p>}{brief.content.sources.map(s=><fieldset key={s.id}><legend>Evidence {s.id} · {s.publisher}</legend><p>{s.relevant_excerpt||'No excerpt retained.'}</p><label><input type="checkbox" disabled={busy} checked={draft.supporting_source_ids.includes(s.id)} onChange={()=>choose(s.id,'supporting_source_ids')}/>Supports decision · evidence {s.id}</label><label><input type="checkbox" disabled={busy} checked={draft.contradicting_source_ids.includes(s.id)} onChange={()=>choose(s.id,'contradicting_source_ids')}/>Contradicts decision · evidence {s.id}</label></fieldset>)}
        <button disabled={busy}>{save.isPending?'Recording…':pending.current?'Retry same decision':'Record reviewer decision'}</button>
      </form>}
    </>}
    {[load.error,save.error].filter(Boolean).map((e,i)=><p role="alert" key={i}>{e!.message} Reload the reviewed brief after a conflicting decision.</p>)}
    <h3>Decision history</h3>{history.data?.items.map(r=><DecisionRecord key={r.id} record={r}/>)}<nav aria-label="Decision history pages"><button disabled={page===1} onClick={()=>setPage(page-1)}>Previous decisions</button><span>Page {page}</span><button disabled={!history.data?.has_next} onClick={()=>setPage(page+1)}>Next decisions</button></nav>
  </section>;
}
