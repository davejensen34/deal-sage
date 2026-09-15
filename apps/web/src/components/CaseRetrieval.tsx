import {useRef} from 'react';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {api} from '../api/client';
import {useIdentity} from './AuthGate';

type Attempt={id:number;source_id:number;status:string;actor:string;evidence_id:number|null;error_code:string|null;recovery_after:string};
type History={provider:string;policy:{max_bytes:number;timeout_seconds:number;max_source_attempts:number;max_case_attempts:number};attempts:Attempt[]};
function useHistory(caseId:number){return useQuery({queryKey:['case-retrievals',caseId],queryFn:()=>api<History>(`/research/cases/${caseId}/investigation/retrievals`),refetchInterval:q=>q.state.data?.attempts?.some(a=>a.status==='running')?1500:false})}
function useRefresh(caseId:number){const qc=useQueryClient();return ()=>{
  qc.invalidateQueries({queryKey:['case-retrievals',caseId]});qc.invalidateQueries({queryKey:['case-investigation',caseId]});
  qc.invalidateQueries({queryKey:['research-case']});qc.invalidateQueries({queryKey:['research-case-narratives']});qc.invalidateQueries({queryKey:['reviewer-inbox']});
}}

export function RetrieveSource({caseId,sourceId,url}:{caseId:number;sourceId:number;url:string}){
  const identity=useIdentity(),history=useHistory(caseId),refresh=useRefresh(caseId);
  const key=useRef<string|null>(null);
  const action=useMutation({mutationFn:()=>{key.current ||= crypto.randomUUID();return api(`/research/cases/${caseId}/investigation/sources/${sourceId}/retrieve`,{method:'POST',body:JSON.stringify({request_key:key.current,expected_url:url})})},onSuccess:()=>{key.current=null},onSettled:refresh});
  const canOperate=!!identity&&['operator','administrator','demo'].includes(identity.role);
  const data=history.data?.policy && history.data?.attempts ? history.data : undefined;
  const active=data?.attempts?.some(a=>a.status==='running');
  const exhausted=!!data&&(data.attempts.length>=data.policy.max_case_attempts||data.attempts.filter(a=>a.source_id===sourceId).length>=data.policy.max_source_attempts);
  return <section><p>Retrieve one document: at most 1 MB and 20 seconds, no redirects or automatic retries. No model calls or source fees. Your discovery limits remain unchanged.</p>
    <p>{data?.provider==='fixture'?'Fictional retrieval; only example.test fictional discovery URLs are supported.':'Operator-authorized public HTTP retrieval after source-access review.'}</p>
    {!canOperate&&<p>An operator is required to retrieve source documents.</p>}
    <button disabled={!canOperate||!data||action.isPending||active||exhausted} onClick={()=>action.mutate()}>{action.isPending?'Retrieving…':key.current?'Retry same retrieval request':'Retrieve one document'}</button>
    {exhausted&&<p>Retrieval attempt ceiling reached; retained evidence and history remain available.</p>}
    {action.error&&<p role="alert">{action.error.message} <button onClick={()=>{key.current=null;history.refetch()}}>Reload retrieval history</button></p>}
    {history.isError&&<p role="alert">Retrieval limits unavailable. <button onClick={()=>history.refetch()}>Try again</button></p>}
  </section>;
}

export function RetrievalHistory({caseId}:{caseId:number}){
  const result=useHistory(caseId),identity=useIdentity(),refresh=useRefresh(caseId);
  const recover=useMutation({mutationFn:(id:number)=>api(`/research/cases/${caseId}/investigation/retrievals/${id}/recover`,{method:'POST'}),onSettled:refresh});
  const canOperate=!!identity&&['operator','administrator','demo'].includes(identity.role);
  return <section><h3>Document retrieval history</h3>{result.isLoading?<p>Loading retrieval history…</p>:result.isError?<p role="alert">Retrieval history unavailable. <button onClick={()=>result.refetch()}>Try again</button></p>:<>
    <p>At most {result.data?.policy?.max_source_attempts} attempts per source and {result.data?.policy?.max_case_attempts} per case, including failures and interrupted attempts. Retrying a failed attempt is a new explicit action.</p>
    {!result.data?.attempts?.length&&<p>No retrieval attempts yet.</p>}
    {result.data?.attempts?.map(a=><article key={a.id} className="investigation-item"><p><b>Attempt {a.id} · source {a.source_id} · {a.status}</b><br/>{a.actor}{a.evidence_id&&` · retained evidence #${a.evidence_id}`}{a.error_code&&` · ${a.error_code.replaceAll('_',' ')}`}</p>
      {a.status==='running'&&<><p>If interrupted, recovery is available after {new Date(a.recovery_after).toLocaleString()}. It retains an unknown outcome and makes no request.</p><button disabled={!canOperate||recover.isPending||Date.parse(a.recovery_after)>Date.now()} onClick={()=>recover.mutate(a.id)}>Recover interrupted retrieval {a.id}</button></>}
    </article>)}
  </>}{recover.error&&<p role="alert">{recover.error.message}</p>}</section>;
}
