import {useRef,useState} from 'react';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {Link} from 'react-router-dom';
import {api} from '../api/client';
import {useIdentity} from './AuthGate';
import '../pages/discovery.css';

type Plan={expected_prior_id:number|null;due_on:string;state:'active'|'paused';question:string;reason:string};
type Record={id:number;case_id:number;prior_id:number|null;actor:string;recorded_at:string;due:boolean;monitoring:Plan};
type History={latest:Record|null;items:Record[];has_next:boolean;as_of:string};

function MonitoringRecord({row,historical=false}:{row:Record;historical?:boolean}) {
  const m=row.monitoring;
  return <article className="investigation-item"><p><b>{historical?'Previous schedule':m.state==='paused'?'Paused':row.due?'Due for manual review':'Scheduled for manual review'}</b> · {m.state} · Review date (UTC): {m.due_on}</p>
    <p><b>Monitoring question:</b> {m.question}</p><p><b>Reason:</b> {m.reason}</p>
    <p>{row.actor} · {new Date(row.recorded_at).toLocaleString()} · record {row.id}{row.prior_id?` · replaces record ${row.prior_id}`:''}</p></article>;
}

export function CaseMonitoring({caseId}:{caseId:number}) {
  const identity=useIdentity(),qc=useQueryClient();
  const [page,setPage]=useState(1),[draft,setDraft]=useState<Plan|null>(null);
  const pending=useRef<{request_key:string;monitoring:Plan}|null>(null);
  const history=useQuery({queryKey:['case-monitoring',caseId,page],queryFn:()=>api<History>(`/monitoring/cases/${caseId}?page=${page}`)});
  const load=useMutation({mutationFn:async()=>{const h=await history.refetch();if(h.error)throw h.error;return h.data!},onSuccess:h=>{pending.current=null;setDraft({expected_prior_id:h.latest?.id??null,due_on:h.latest?.monitoring.due_on??h.as_of,state:h.latest?.monitoring.state??'active',question:h.latest?.monitoring.question??'',reason:''})}});
  const save=useMutation({mutationFn:()=>{pending.current||={request_key:crypto.randomUUID(),monitoring:draft!};return api<Record>(`/monitoring/cases/${caseId}`,{method:'POST',body:JSON.stringify(pending.current)})},onSuccess:()=>{pending.current=null;setDraft(null);setPage(1);qc.invalidateQueries({queryKey:['case-monitoring',caseId]});qc.invalidateQueries({queryKey:['monitoring-queue']})}});
  const edit=(v:Partial<Plan>)=>{pending.current=null;setDraft({...draft!,...v})};
  const busy=save.isPending||load.isPending,canEdit=!!identity&&identity.role!=='viewer';
  return <section className="panel case-investigation monitoring-panel"><h2>My case monitoring</h2><p>Keep this case for manual review even when no business or candidate is established. Dates and questions belong to your signed-in identity. This does not run searches, send notifications or change the shared reviewer decision.</p>
    <Link to="/watchlists">Open my monitoring queue</Link>
    {history.isLoading?<p>Loading monitoring…</p>:history.isError?<p role="alert">Monitoring unavailable. <button onClick={()=>history.refetch()}>Reload monitoring</button></p>:history.data?.latest?<MonitoringRecord row={history.data.latest}/>:<p>This case is not in your monitoring queue.</p>}
    {canEdit&&<><button disabled={busy||!history.data||history.isError} onClick={()=>load.mutate()}>{draft?'Reload current monitoring':'Set up or update monitoring'}</button>
      {draft&&<form className="discovery-form" onSubmit={e=>{e.preventDefault();save.mutate()}}>
        <label>Review date (UTC)<input type="date" required disabled={busy} value={draft.due_on} onChange={e=>edit({due_on:e.target.value})}/></label>
        <label>Monitoring state<select disabled={busy} value={draft.state} onChange={e=>edit({state:e.target.value as Plan['state']})}><option value="active">Active</option><option value="paused">Paused</option></select></label>
        <label>Question to revisit<input required minLength={10} maxLength={1000} disabled={busy} value={draft.question} onChange={e=>edit({question:e.target.value})}/></label>
        <label>Reason for this schedule<input required minLength={10} maxLength={1000} disabled={busy} value={draft.reason} onChange={e=>edit({reason:e.target.value})}/></label>
        <p>Active items are due on or before today’s UTC date. Paused items retain their date and history. Saving a date does not record that a review was completed.</p>
        <button disabled={busy}>{save.isPending?'Saving…':pending.current?'Retry same monitoring update':'Save monitoring'}</button>
      </form>}
    </>}
    {[load.error,save.error].filter(Boolean).map((e,i)=><p role="alert" key={i}>{e!.message}</p>)}
    <details><summary>Monitoring history</summary><p>Earlier records are retained history, not additional active reminders.</p>
      {history.data?.items.map(row=><MonitoringRecord key={row.id} row={row} historical={row.id!==history.data?.latest?.id}/>)}
      <nav aria-label="Monitoring history pages"><button disabled={page===1} onClick={()=>setPage(page-1)}>Previous monitoring records</button> Page {page} <button disabled={!history.data?.has_next} onClick={()=>setPage(page+1)}>Next monitoring records</button></nav>
    </details>
  </section>;
}

export function MonitoringQueue() {
  const [scope,setScope]=useState('due'),[page,setPage]=useState(1);
  const result=useQuery({queryKey:['monitoring-queue',scope,page],queryFn:()=>api<{items:Record[];has_next:boolean;due_count:number;as_of:string}>(`/monitoring/cases?scope=${scope}&page=${page}`)});
  return <section className="panel case-investigation monitoring-panel"><h2>My monitored research cases</h2><p>Unresolved cases can be retained here without candidate promotion. Open a case to set a review date or update its monitoring question. This queue does not perform research.</p>
    <Link to="/">Find a case in the reviewer inbox</Link>
    <label> Show monitoring <select value={scope} onChange={e=>{setScope(e.target.value);setPage(1)}}><option value="due">Due</option><option value="active">All active</option><option value="paused">Paused</option><option value="all">All monitored cases</option></select></label>
    {result.isError?<p role="alert">Monitoring queue unavailable. <button onClick={()=>result.refetch()}>Reload queue</button></p>:result.isLoading?<p>Loading monitoring queue…</p>:<><p>{result.data?.due_count} {result.data?.due_count===1?'case':'cases'} due as of {result.data?.as_of} (UTC).</p>
      {!result.data?.items.length&&<p>No cases in this monitoring view.</p>}
      {result.data?.items.map(row=><div key={row.id}><Link to={`/research/cases/${row.case_id}`}>Open monitored case {row.case_id}</Link><MonitoringRecord row={row}/></div>)}
    </>}
    <nav aria-label="Monitoring queue pages"><button disabled={page===1} onClick={()=>setPage(page-1)}>Previous monitored cases</button> Page {page} <button disabled={!result.data?.has_next} onClick={()=>setPage(page+1)}>Next monitored cases</button></nav>
  </section>;
}
