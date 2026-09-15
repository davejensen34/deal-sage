import {useRef, useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {Link, useNavigate, useParams} from 'react-router-dom';
import {api} from '../api/client';
import {useIdentity} from '../components/AuthGate';
import './discovery.css';

type Config={origin:string;objective:string;business_name:string;states:string[];signals:string[];lookback_days:number;max_records:number;max_queries:number;max_cost_cents:number;max_elapsed_seconds:number};
type Plan={question?:string;rationale?:string;version:string;settings:Config;policy:{assessment_date:string};queries:string[];submitted_queries:string[];provider:{key:string;model:string|null;ready:boolean;reason:string;reservation_cents:number;max_results:number;timeout_seconds:number}};
type Attempt={id:number;request_key:string;slot:number;status:string;reserved_cents:number;result_count:number|null;error_code:string|null;actor:string;recovery_after:string};
type Run={id:number;case_id:number;plan:Plan;status:string;revision:number;next_slot:number;reserved_cents:number;record_count:number;deadline_at:string|null;attempts:Attempt[]};
const words=(s:string)=>s.replaceAll('_',' ');
const families=['possible_death','retirement','succession','ownership_change','founder_exit','dissolution','restructuring','leadership_change'];
const money=(c:number)=>`$${(c/100).toFixed(2)}`;

function PlanSummary({plan}:{plan:Plan}) {
  return <section className="panel discovery-plan"><h2>{plan.question?'Bounded follow-up plan':'Bounded discovery plan'}</h2>{plan.question&&<><h3>{plan.question}</h3><p>{plan.rationale}</p></>}
    <p>{plan.provider.reason}{plan.provider.model&&` · ${plan.provider.model}`}</p>
    <p>{plan.settings.max_records} unique source links maximum · {plan.settings.max_queries} total attempts including retries · {money(plan.settings.max_cost_cents)} reservation ceiling</p>
    <p>{money(plan.provider.reservation_cents)} reserved per attempt, including failures. This is a conservative reservation, not a measured invoice. Up to {plan.provider.max_results} links per query.</p>
    <p>{plan.settings.lookback_days}-day lookback assessed {plan.policy.assessment_date}. Time ceiling starts with the first attempt: {plan.settings.max_elapsed_seconds} seconds.</p>
    <details><summary>Review exact search queries ({plan.queries.length})</summary><ol>{plan.submitted_queries.map((q,i)=><li key={i}>{q}</li>)}</ol></details>
    <p>Search results are unverified clues. Discovery does not retrieve pages, prove ownership, promote candidates or send messages. Evidence investigation follows separately.</p>
  </section>;
}

export function Discovery() {
  const identity=useIdentity(), navigate=useNavigate(), qc=useQueryClient();
  const canPrepare=!!identity&&identity.role!=='viewer';
  const canOperate=!!identity&&['operator','administrator','demo'].includes(identity.role);
  const defaults=useQuery({queryKey:['discovery-defaults'],queryFn:()=>api<{profile_id:number|null;settings:Config}>('/discovery/defaults')});
  const [config,setConfig]=useState<Config|null>(null), [prepared,setPrepared]=useState<{plan:Plan;hash:string}|null>(null), [page,setPage]=useState(1);
  const key=useRef<string|null>(null);
  const value=config||defaults.data?.settings;
  const requiredQueries=value ? value.states.length*value.signals.length : 0;
  const selectionMissing=requiredQueries===0;
  const capacityShort=!!value && value.max_queries<requiredQueries;
  const scopeInvalid=selectionMissing||capacityShort;
  const history=useQuery({queryKey:['discovery-runs',page],queryFn:()=>api<{items:{id:number;case_id:number;objective:string;status:string}[];has_next:boolean}>(`/discovery/runs?page=${page}`)});
  const inspect=useMutation({mutationFn:()=>api<{plan:Plan;hash:string}>('/discovery/preview',{method:'POST',body:JSON.stringify(value)}),onSuccess:p=>{setPrepared(p);key.current=crypto.randomUUID()}});
  const create=useMutation({mutationFn:()=>api<Run>('/discovery/runs',{method:'POST',body:JSON.stringify({settings:value,profile_id:defaults.data?.profile_id,expected_hash:prepared!.hash,request_key:key.current})}),onSuccess:r=>{qc.invalidateQueries({queryKey:['reviewer-inbox']});navigate(`/discover/runs/${r.id}`)}});
  const save=useMutation({mutationFn:()=>api('/discovery/defaults',{method:'POST',body:JSON.stringify(value)}),onSuccess:()=>qc.invalidateQueries({queryKey:['discovery-defaults']})});
  const change=(field:keyof Config,next:unknown)=>{setConfig({...value!,[field]:next});setPrepared(null);inspect.reset();create.reset();save.reset()};
  const errors=[inspect.error,create.error,save.error].filter(Boolean);
  return <div className="discovery-page"><div className="page-heading"><div><p className="eyebrow">Discover</p><h1>Find business transitions</h1><p>Define what you want to learn, review the scope, then save a bounded plan.</p></div></div>
    {defaults.isError?<section role="alert" className="panel"><h2>Discovery defaults unavailable</h2><button onClick={()=>defaults.refetch()}>Try again</button></section>:!value?<p role="status">Loading saved defaults…</p>:<form className="panel discovery-form" onSubmit={e=>{e.preventDefault();if(!scopeInvalid)inspect.mutate()}}>
      <label>Starting point<select value={value.origin} disabled={!canPrepare} onChange={e=>change('origin',e.target.value)}><option value="signal_first">Find transition events</option><option value="business_first">Research a business</option><option value="hybrid">Explore a market / hybrid</option></select></label>
      <label>Research objective<input required minLength={10} maxLength={160} value={value.objective} onChange={e=>change('objective',e.target.value)}/></label>
      <label>Business name {value.origin==='business_first'?'(required)':'(optional)'}<input required={value.origin==='business_first'} maxLength={100} value={value.business_name} onChange={e=>change('business_name',e.target.value)}/></label>
      <fieldset><legend>States</legend>{['CO','UT','TX'].map(s=><label key={s}><input type="checkbox" checked={value.states.includes(s)} onChange={e=>change('states',e.target.checked?[...value.states,s]:value.states.filter(x=>x!==s))}/>{s}</label>)}</fieldset>
      <fieldset><legend>Transition families</legend>{families.map(s=><label key={s}><input type="checkbox" checked={value.signals.includes(s)} onChange={e=>change('signals',e.target.checked?[...value.signals,s]:value.signals.filter(x=>x!==s))}/>{words(s)}</label>)}</fieldset>
      <div className="discovery-limits">{[['lookback_days','Lookback days',1,365],['max_records','Maximum source links',1,100],['max_queries','Total query attempts (including retries)',1,30],['max_cost_cents','Reservation ceiling (USD cents)',0,500],['max_elapsed_seconds','Elapsed-time ceiling (seconds)',60,3600]].map(([field,label,min,max])=><label key={field}>{label}<input type="number" required min={Number(min)} max={Number(max)} aria-describedby={field==='max_queries'?'discovery-query-capacity':undefined} aria-invalid={field==='max_queries'&&capacityShort||undefined} value={value[field as keyof Config] as number} onChange={e=>change(field as keyof Config,Number(e.target.value))}/></label>)}</div>
      <section aria-live="polite" aria-atomic="true" id="discovery-query-capacity">
        <p><strong>{value.states.length} {value.states.length===1?'state':'states'} × {value.signals.length} transition {value.signals.length===1?'family':'families'} = {requiredQueries} planned {requiredQueries===1?'query':'queries'}.</strong></p>
        {selectionMissing?<p>Select at least one state and one transition family to prepare a plan.</p>:capacityShort?<>
          <p>Your selections need {requiredQueries} query attempts; the current limit is {value.max_queries}. Increase the attempt limit or select fewer states or families.</p>
          <button type="button" disabled={!canPrepare} onClick={()=>change('max_queries',requiredQueries)}>Set attempt limit to {requiredQueries}</button>
        </>:<p>{value.max_queries-requiredQueries} additional {value.max_queries-requiredQueries===1?'attempt':'attempts'} available for retries.</p>}
        <p>Changing the attempt limit does not change your reservation ceiling or run a search. The preview shows provider costs; execution may stop earlier at your cost, time or source-link limit.</p>
      </section>
      <div className="discovery-actions"><button className="primary" disabled={!canPrepare||inspect.isPending||scopeInvalid}>Preview plan</button><button type="button" disabled={!canOperate||save.isPending||scopeInvalid} onClick={()=>{if(!scopeInvalid)save.mutate()}}>Save as workspace defaults</button></div>
      {save.isSuccess&&<p role="status">Saved a new defaults version. Existing runs are unchanged.</p>}
    </form>}
    {errors.map((e,i)=><p role="alert" key={i}>{e!.message}</p>)}
    {prepared&&<><PlanSummary plan={prepared.plan}/><button className="primary" disabled={create.isPending} onClick={()=>create.mutate()}>Save research plan</button><p>Saving creates a research case. An operator authorizes execution from its run page.</p></>}
    <section className="panel discovery-history"><h2>Saved discovery runs</h2>{history.isError?<p role="alert">Run history is unavailable. <button onClick={()=>history.refetch()}>Try again</button></p>:history.isLoading?<p>Loading runs…</p>:<>{!history.data?.items.length&&<p>No runs saved yet.</p>}{history.data?.items.map(r=><p key={r.id}><Link to={`/discover/runs/${r.id}`}>Run {r.id}: {r.objective}</Link> · {r.status}</p>)}<button disabled={page===1} onClick={()=>setPage(page-1)}>Previous runs</button><button disabled={!history.data?.has_next} onClick={()=>setPage(page+1)}>Next runs</button></>}</section>
  </div>;
}

export function DiscoveryRun({followup=false}:{followup?:boolean}) {
  const resource=followup?'followups':'discovery';
  const {id}=useParams(),identity=useIdentity(),qc=useQueryClient();
  const canOperate=!!identity&&['operator','administrator','demo'].includes(identity.role);
  const [executing,setExecuting]=useState(false);
  const pending=useRef<{request_key:string;expected_revision:number;retry_last:boolean}|null>(null);
  const result=useQuery({queryKey:[resource+'-run',id],queryFn:()=>api<Run>(`/${resource}/runs/${id}`),retry:false,
    refetchInterval:q=>executing||q.state.data?.status==='running'?1500:false});
  const refresh=()=>{qc.invalidateQueries({queryKey:[resource+'-run',id]});qc.invalidateQueries({queryKey:['reviewer-inbox']});qc.invalidateQueries({queryKey:['research-case']})};
  const execute=useMutation({mutationFn:(retry:boolean)=>{
    pending.current ||= {request_key:crypto.randomUUID(),expected_revision:result.data!.revision,retry_last:retry};
    return api<Run>(`/${resource}/runs/${id}/execute`,{method:'POST',body:JSON.stringify(pending.current)});
  },onMutate:()=>setExecuting(true),onSuccess:r=>{pending.current=null;qc.setQueryData([resource+'-run',id],r);refresh()},onSettled:()=>{setExecuting(false);refresh()}});
  const recover=useMutation({mutationFn:()=>api(`/${resource}/runs/${id}/recover`,{method:'POST',body:JSON.stringify({expected_revision:result.data!.revision})}),onSuccess:()=>{pending.current=null;refresh()}});
  if(result.isLoading)return <p role="status">Loading durable run progress…</p>;
  if(result.isError||!result.data)return <section className="panel" role="alert"><h1>Discovery run unavailable</h1><p>{result.error?.message}</p><Link to="/discover">Back to discovery</Link></section>;
  const run=result.data,last=run.attempts.at(-1),cfg=run.plan.settings;
  const exhausted=run.attempts.length>=cfg.max_queries||run.record_count>=cfg.max_records||run.reserved_cents+run.plan.provider.reservation_cents>cfg.max_cost_cents||!!run.deadline_at&&Date.parse(run.deadline_at)<Date.now();
  const disabled=!canOperate||executing||run.status==='running'||exhausted||!run.plan.provider.ready;
  return <div className="discovery-page"><Link to="/discover">← Discovery setup & history</Link><h1>{followup?'Follow-up search':'Discovery run'} {run.id}</h1>{followup&&<p>Search completion does not resolve the research question. Review discovered clues in the case, then explicitly retrieve evidence and save a new brief version.</p>}
    <section className="panel"><h2>Status: {run.status}</h2><p>{run.next_slot} of {run.plan.queries.length} planned slots attempted · {run.record_count} unverified links retained · {money(run.reserved_cents)} reserved</p>
      <p><Link to={`/research/cases/${run.case_id}`}>Review case {run.case_id} and discovered clues →</Link></p>
      <div className="discovery-actions"><button className="primary" disabled={disabled||run.next_slot>=run.plan.queries.length} onClick={()=>execute.mutate(false)}>{executing?'Searching…':pending.current?'Retry same request':'Run next search'}</button>
        {last?.status==='failed'&&<button disabled={disabled} onClick={()=>execute.mutate(true)}>Retry failed search within remaining budget</button>}
        <button onClick={()=>{pending.current=null;result.refetch()}}>Reload progress</button>
        {run.status==='running'&&<button disabled={!canOperate||recover.isPending||!last||Date.parse(last.recovery_after)>Date.now()} onClick={()=>recover.mutate()}>Recover interrupted attempt without replay</button>}
      </div>
      {exhausted&&<p>Run ceiling reached. Retained outcomes and reservations remain available.</p>}
      {!canOperate&&<p>An operator is required to execute or recover searches.</p>}
      <p>One explicit search per action. Browser disconnection does not release a reservation. Recovery retains an unknown outcome and skips that query; it makes no new call.</p>
      {[execute.error,recover.error].filter(Boolean).map((e,i)=><p role="alert" key={i}>{e!.message}</p>)}
    </section>
    <PlanSummary plan={run.plan}/>
    <section className="panel"><h2>Attempt history</h2>{!run.attempts.length&&<p>No attempts yet. No budget reserved.</p>}{run.attempts.map(a=><article className="discovery-attempt" key={a.id}><h3>Attempt {a.id} · query {a.slot+1} · {a.status}</h3><p>{a.actor} · {money(a.reserved_cents)} reserved · results: {a.result_count??'unknown'}</p>{a.error_code&&<p>{words(a.error_code)}</p>}{a.status==='running'&&<p>Recovery available after {new Date(a.recovery_after).toLocaleString()} if execution was interrupted.</p>}</article>)}</section>
  </div>;
}
