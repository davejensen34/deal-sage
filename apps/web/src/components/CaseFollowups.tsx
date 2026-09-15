import {useRef,useState} from 'react';
import {useMutation,useQuery} from '@tanstack/react-query';
import {Link,useNavigate} from 'react-router-dom';
import {api} from '../api/client';
import {useIdentity} from './AuthGate';
import '../pages/discovery.css';

type Input={question:string;rationale:string;query:string};
type Preview={hash:string;plan:{submitted_queries:string[];provider:{reason:string;reservation_cents:number};settings:{max_records:number}}};
export function CaseFollowups({caseId}:{caseId:number}){
  const identity=useIdentity(),navigate=useNavigate(),key=useRef<string|null>(null);
  const [value,setValue]=useState<Input>({question:'',rationale:'',query:''});
  const [prepared,setPrepared]=useState<Preview|null>(null);
  const history=useQuery({queryKey:['case-followups',caseId],queryFn:()=>api<{items:{id:number;question:string;actor:string;status:string}[]}>(`/followups/cases/${caseId}`)});
  const preview=useMutation({mutationFn:()=>api<Preview>(`/followups/cases/${caseId}/preview`,{method:'POST',body:JSON.stringify(value)}),onSuccess:p=>{setPrepared(p);key.current=crypto.randomUUID()}});
  const create=useMutation({mutationFn:()=>api<{id:number}>(`/followups/cases/${caseId}`,{method:'POST',body:JSON.stringify({settings:value,request_key:key.current,expected_hash:prepared!.hash})}),onSuccess:r=>navigate(`/followups/runs/${r.id}`)});
  const canReview=!!identity&&identity.role!=='viewer';
  return <section className="panel case-investigation"><h2>Research a specific unknown</h2><p>Record your question and why it matters, then review the exact search. Finding a link does not answer the question or verify ownership.</p>
    <form className="discovery-form" onSubmit={e=>{e.preventDefault();preview.mutate()}}>
      {(['question','rationale','query'] as const).map(name=><label key={name}>{name==='question'?'Follow-up question':name==='rationale'?'Why this needs research':'Exact search query'}<input required minLength={name==='query'?5:10} maxLength={name==='query'?350:name==='question'?500:1000} value={value[name]} disabled={create.isPending||preview.isPending} onChange={e=>{setValue({...value,[name]:e.target.value});setPrepared(null);key.current=null}}/></label>)}
      <button disabled={!canReview||preview.isPending||create.isPending}>Preview follow-up</button>
    </form>
    {prepared&&<section><h3>Follow-up authorization preview</h3><p>{prepared.plan.provider.reason}</p><blockquote>{prepared.plan.submitted_queries[0]}</blockquote><p>One planned query; at most two attempts including an explicit failed retry. Up to 10 additional links, within a {prepared.plan.settings.max_records}-link total case ceiling for this plan. Ten-minute time ceiling; 24 USD cents maximum, {prepared.plan.provider.reservation_cents} cents reserved per attempt.</p><p>Across this case: ten follow-up plans, twenty attempts and 240 USD cents maximum. Original discovery limits stay unchanged. Creation makes no external call; an operator executes the saved plan.</p><button disabled={!canReview||create.isPending||preview.isPending} onClick={()=>create.mutate()}>Save follow-up plan</button></section>}
    {[preview.error,create.error].filter(Boolean).map((e,i)=><p role="alert" key={i}>{e!.message}</p>)}
    <h3>Saved follow-ups</h3>{history.isLoading?<p>Loading follow-ups…</p>:history.isError?<p role="alert">Follow-ups unavailable. <button onClick={()=>history.refetch()}>Retry history</button></p>:!history.data?.items.length?<p>No saved follow-ups yet.</p>:history.data.items.map(r=><p key={r.id}><Link to={`/followups/runs/${r.id}`}>{r.question}</Link> · {r.actor} · {r.status}</p>)}
  </section>;
}
