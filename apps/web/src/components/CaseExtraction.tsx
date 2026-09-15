import {useRef,useState} from 'react';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {api} from '../api/client';
import {useIdentity} from './AuthGate';

type Policy={provider:string;model:string;ready:boolean;reason:string;reserved_cents:number;max_output_tokens:number;timeout_seconds:number;max_attempts:number;max_cost_cents:number};
type Packet={evidence_id:number;excerpt:string;content_hash:string;publisher:string;published_at:string|null};
type Preview={plan_hash:string;plan:{policy:Policy;packet:Packet}};
type Output={observations:{field:string;value:string;quote:string;certainty:string}[];unresolved_questions:string[]};
type Attempt={id:number;evidence_id:number;actor:string;status:string;error_code:string|null;reserved_cents:number;recovery_after:string;policy:Policy;packet:Packet;proposal:null|{id:number;outcome:string;output:Output|null;input_tokens:number|null;output_tokens:number|null;cost_cents:number}};
type History={policy:Policy;attempts:Attempt[]};
function useHistory(caseId:number){return useQuery({queryKey:['case-extractions',caseId],queryFn:()=>api<History>(`/research/cases/${caseId}/investigation/extractions`),refetchInterval:q=>q.state.data?.attempts?.some(a=>a.status==='running')?1500:false})}
function useRefresh(caseId:number){const qc=useQueryClient();return ()=>{
  qc.invalidateQueries({queryKey:['case-extractions',caseId]});qc.invalidateQueries({queryKey:['research-case']});qc.invalidateQueries({queryKey:['research-case-narratives']});
}}
function useOperator(){const identity=useIdentity();return !!identity&&['operator','administrator','demo'].includes(identity.role)}

export function ExtractEvidence({caseId,evidenceId}:{caseId:number;evidenceId:number}){
  const [expanded,setExpanded]=useState(false),[frozen,setFrozen]=useState<Preview|null>(null);
  const key=useRef<string|null>(null),canOperate=useOperator(),refresh=useRefresh(caseId);
  const preview=useMutation({mutationFn:()=>api<Preview>(`/research/cases/${caseId}/investigation/evidence/${evidenceId}/extraction-preview`),onSuccess:p=>{setFrozen(p);key.current=null}});
  const execute=useMutation({mutationFn:()=>{key.current ||= crypto.randomUUID();return api(`/research/cases/${caseId}/investigation/evidence/${evidenceId}/extract`,{method:'POST',body:JSON.stringify({request_key:key.current,expected_hash:frozen?.plan_hash})})},onSuccess:()=>{key.current=null;setFrozen(null)},onSettled:refresh});
  const limits=frozen?.plan.policy;
  return <section><button aria-expanded={expanded} onClick={()=>setExpanded(!expanded)}>{expanded?'Hide':'Prepare'} extraction for evidence {evidenceId}</button>{expanded&&<>
    <p>Extract reported business and transition details from this retained excerpt. Output is a cited model interpretation, not a source fact or human judgment. No search, source retrieval, score change or promotion occurs.</p>
    <button disabled={preview.isPending||execute.isPending} onClick={()=>{setFrozen(null);preview.mutate()}}>Preview extraction packet</button>
    {preview.error&&<p role="alert">{preview.error.message}</p>}
    {frozen&&limits&&<><p><b>{limits.reason}</b> · {limits.model}</p><p>One call · {limits.max_output_tokens} output tokens · {limits.timeout_seconds} seconds · no automatic retries · reserve {limits.reserved_cents} USD cents. Case ceiling: {limits.max_attempts} attempts and {limits.max_cost_cents} USD cents, including retained reservations and prior model work.</p>
      <details><summary>Exact retained excerpt to extract</summary><blockquote>{frozen.plan.packet.excerpt}</blockquote><p>Source evidence {evidenceId} · SHA-256 <code>{frozen.plan.packet.content_hash}</code></p></details>
      <p>{limits.provider==='fixture'?'Offline fictional fixture. No data leaves DealSage.':'This action sends the displayed retained packet to OpenAI. Provider-side response storage is disabled.'}</p>
      {!canOperate&&<p>An operator is required to authorize model execution.</p>}
      <button disabled={!canOperate||!limits.ready||execute.isPending} onClick={()=>execute.mutate()}>{execute.isPending?'Extracting…':key.current?'Retry same extraction request':'Authorize one extraction'}</button>
    </>}
    {execute.error&&<p role="alert">{execute.error.message} Check extraction history before creating a new request.</p>}
  </>}</section>;
}

export function ExtractionHistory({caseId}:{caseId:number}){
  const result=useHistory(caseId),canOperate=useOperator(),refresh=useRefresh(caseId);
  const recovery=useMutation({mutationFn:(id:number)=>api(`/research/cases/${caseId}/investigation/extractions/${id}/recover`,{method:'POST'}),onSettled:refresh});
  return <section><h3>Cited extraction history</h3><p>Model observations retain their exact source quotation. A matching quote does not verify the model's interpretation, ownership or sale intent. Empty output remains useful as an explicit unresolved result.</p>
    {result.isLoading?<p>Loading extraction history…</p>:result.isError?<p role="alert">Extraction history unavailable. <button onClick={()=>result.refetch()}>Try again</button></p>:<>
      {!result.data?.attempts?.length&&<p>No extraction attempts yet.</p>}
      {result.data?.attempts?.map(a=><article className="investigation-item" key={a.id}><h4>Extraction {a.id} · evidence {a.evidence_id} · {a.status}</h4>
        <p>{a.actor} · {a.policy.provider} / {a.policy.model} · reserved {a.reserved_cents} USD cents{a.error_code&&` · ${a.error_code.replaceAll('_',' ')}`}</p>
        {a.status==='running'&&<><p>Recovery available after {new Date(a.recovery_after).toLocaleString()}; it records an unknown outcome without refund or replay.</p><button disabled={!canOperate||recovery.isPending||Date.parse(a.recovery_after)>Date.now()} onClick={()=>recovery.mutate(a.id)}>Recover interrupted extraction {a.id}</button></>}
        {a.proposal&&<><p>Model proposal #{a.proposal.id} · input tokens: {a.proposal.input_tokens??'unknown'} · output tokens: {a.proposal.output_tokens??'unknown'} · estimated cost: {a.proposal.input_tokens===null||a.proposal.output_tokens===null?'unknown':`${a.proposal.cost_cents} USD cents`}</p>
          {a.proposal.output&&<>{!a.proposal.output.observations.length&&<p>No supported observations extracted.</p>}{a.proposal.output.observations.map((o,i)=><div key={i}><p><b>{o.field.replaceAll('_',' ')}: {o.value}</b> · model interpretation · {o.certainty.replaceAll('_',' ')}</p><blockquote>{o.quote}</blockquote><p>Quote from retained evidence {a.evidence_id}; field meaning remains unverified.</p></div>)}
          <h4>Unresolved questions</h4>{a.proposal.output.unresolved_questions.map((q,i)=><p key={i}>{q}</p>)}</>}
        </>}
        <details><summary>Frozen source excerpt for extraction {a.id}</summary><blockquote>{a.packet.excerpt}</blockquote><p>Evidence {a.packet.evidence_id} · hash <code>{a.packet.content_hash}</code></p></details>
      </article>)}
    </>}{recovery.error&&<p role="alert">{recovery.error.message}</p>}
  </section>;
}
