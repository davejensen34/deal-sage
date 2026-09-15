import {useRef,useState} from 'react';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {api} from '../api/client';
import {useIdentity} from './AuthGate';
type Policy={assessment_date:string;lookback_days:number};
type Preview={before:Policy|null;after:Policy;hash:string;changed:boolean;history:{id:number;actor:string;reason:string;before:Policy|null;after:Policy}[];has_next:boolean};
const describe=(p:Policy|null)=>p?`${p.lookback_days} days assessed ${p.assessment_date}`:'No date policy';
export function CaseDatePolicy({caseId}:{caseId:number}){
  const [open,setOpen]=useState(false),[page,setPage]=useState(1),[reason,setReason]=useState('');
  const pending=useRef<{request_key:string;expected_hash:string;reason:string}|null>(null);
  const identity=useIdentity(),qc=useQueryClient();
  const q=useQuery({queryKey:['case-date-policy',caseId,page],queryFn:()=>api<Preview>(`/followups/cases/${caseId}/date-policy?page=${page}`),enabled:open});
  const save=useMutation({mutationFn:()=>{pending.current||={request_key:crypto.randomUUID(),expected_hash:q.data!.hash,reason};return api(`/followups/cases/${caseId}/date-policy`,{method:'POST',body:JSON.stringify(pending.current)})},onSuccess:()=>{pending.current=null;setReason('');qc.invalidateQueries()}});
  return <section><button onClick={()=>setOpen(!open)} aria-expanded={open}>{open?'Hide':'Review'} research date window</button>{open&&<>
    {q.isLoading?<p>Loading date window…</p>:q.isError?<p role="alert">{q.error.message} <button onClick={()=>q.refetch()}>Reload window</button></p>:q.data&&<>
      <p>Current: {describe(q.data.before)}. Proposed: {describe(q.data.after)}.</p><p>Renewal changes current date-based routing and future search windows. It does not make old evidence recent, verify a transition or run research. Saved briefs and old plans stay frozen; obsolete plans require a new follow-up. Save a new brief to retain the renewed assessment.</p>
      {identity&&identity.role!=='viewer'&&q.data.changed?<form className="discovery-form" onSubmit={e=>{e.preventDefault();save.mutate()}}><label>Reason for renewing date window<input required minLength={10} maxLength={1000} value={reason} disabled={save.isPending} onChange={e=>{pending.current=null;setReason(e.target.value)}}/></label><button disabled={save.isPending}>{pending.current?'Retry same renewal':'Confirm date-window renewal'}</button></form>:<p>{q.data.changed?'A reviewer can renew this date window.':'The date window is current.'}</p>}
      <h4>Date-window history</h4>{!q.data.history.length&&<p>No renewals recorded.</p>}{q.data.history.map(r=><p key={r.id}>{r.actor}: {describe(r.before)} → {describe(r.after)}. {r.reason}</p>)}
      <button disabled={page===1} onClick={()=>setPage(page-1)}>Previous renewals</button><button disabled={!q.data.has_next} onClick={()=>setPage(page+1)}>Next renewals</button>
    </>}{save.error&&<p role="alert">{save.error.message}</p>}{save.isSuccess&&<p>Date window renewed; no research was executed.</p>}
  </>}</section>;
}
