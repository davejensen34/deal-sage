import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {AlertTriangle,Bell,BellOff,CheckCircle2,Clock3,RefreshCw,ShieldCheck} from 'lucide-react';
import {api} from '../api/client';
import {fmt} from './Status';
import '../source-refresh.css';

export type SourceRefresh={id:number;source_key:string;jurisdiction:string;requested_by:string;status:string;record_limit:number;approved_cost_usd:number;actual_cost_usd:number;freshness_status:string;freshness_reason?:string;error_code?:string;acquisition_run_id?:number;started_at:string;finished_at?:string;result_summary:Record<string,any>};
type Subscription={id:number;source_key:string;event_types:string[];active:boolean};
export type RefreshAlert={id:number;source_refresh_id:number;event_type:string;title:string;detail:string;created_at:string;read_at?:string;trigger?:SourceRefresh&{quarantine_references:{count:number;curated_record_ids:number[];contains_record_content:boolean}}};

const label=(value:string)=>value.replaceAll('_',' ');

export function RefreshHistory({rows}:{rows:SourceRefresh[]}){
  if(!rows.length)return <p className="muted">No analyst-initiated refresh has run yet.</p>;
  return <div className="refresh-history">{rows.map(row=><article id={`refresh-${row.id}`} key={row.id}><div className={`refresh-state ${row.status}`}>{row.status==='succeeded'?<CheckCircle2/>:row.status==='failed'?<AlertTriangle/>:<Clock3/>}</div><div><b>{row.jurisdiction} · {label(row.status)}</b><span>Refresh #{row.id} · {row.requested_by} · {row.record_limit} record limit · {fmt(row.started_at)}</span><small>{label(row.freshness_status)}{row.freshness_reason&&` — ${row.freshness_reason}`}</small></div><dl><dt>Retrieved</dt><dd>{row.result_summary.retrieved??'—'}</dd><dt>Curated</dt><dd>{row.result_summary.curated??'—'}</dd><dt>Cost</dt><dd>${row.actual_cost_usd.toFixed(2)}</dd></dl></article>)}</div>
}

export function AlertInbox({alerts,onRead}:{alerts:RefreshAlert[];onRead?:(id:number)=>void}){
  if(!alerts.length)return <p className="muted">No subscribed refresh issue has been detected.</p>;
  return <div className="alert-inbox">{alerts.map(alert=><article className={alert.read_at?'read':'unread'} key={alert.id}><AlertTriangle/><div><b>{alert.title}</b><span>{alert.detail}</span>{alert.trigger&&<><small>{alert.trigger.source_key.replaceAll('_',' ')} · {label(alert.trigger.freshness_status)} · acquisition run {alert.trigger.acquisition_run_id??'unavailable'}</small><small>{alert.trigger.quarantine_references.count} quarantined · safe record references {alert.trigger.quarantine_references.curated_record_ids.join(', ')||'none'}</small><a href={`#refresh-${alert.source_refresh_id}`}>View refresh #{alert.source_refresh_id} context</a></>}<small>{label(alert.event_type)} · {fmt(alert.created_at)}</small></div>{!alert.read_at&&<button onClick={()=>onRead?.(alert.id)}>Mark read</button>}</article>)}</div>
}

export function SourceRefreshes(){
  const qc=useQueryClient();
  const {data=[]}=useQuery({queryKey:['source-refreshes'],queryFn:()=>api<SourceRefresh[]>('/research/source-refreshes')});
  const {data:subscriptions=[]}=useQuery({queryKey:['alert-subscriptions'],queryFn:()=>api<Subscription[]>('/research/alert-subscriptions')});
  const {data:alerts=[]}=useQuery({queryKey:['refresh-alerts'],queryFn:()=>api<RefreshAlert[]>('/research/alerts')});
  const run=useMutation({mutationFn:(source_key:string)=>api('/research/source-refreshes',{method:'POST',body:JSON.stringify({source_key,record_limit:25,approved_cost_usd:0})}),onSuccess:()=>{qc.invalidateQueries({queryKey:['source-refreshes']});qc.invalidateQueries({queryKey:['refresh-alerts']})}});
  const subscription=useMutation({mutationFn:({source_key,id}:{source_key:string,id?:number})=>id?api(`/research/alert-subscriptions/${id}`,{method:'DELETE'}):api('/research/alert-subscriptions',{method:'POST',body:JSON.stringify({source_key,event_types:['refresh_failed','quarantine_detected']})}),onSuccess:()=>qc.invalidateQueries({queryKey:['alert-subscriptions']})});
  const markRead=useMutation({mutationFn:(id:number)=>api(`/research/alerts/${id}/read`,{method:'PATCH'}),onSuccess:()=>qc.invalidateQueries({queryKey:['refresh-alerts']})});
  const toggle=(source_key:string)=>{const existing=subscriptions.find(item=>item.source_key===source_key&&item.active);subscription.mutate({source_key,id:existing?.id})};
  return <><section className="panel source-refreshes"><div className="panel-title"><div><p className="eyebrow">Milestone 5 · explicit refresh</p><h2>Bounded source refresh</h2><p>Each run is analyst-initiated, limited to 25 records, and approved for $0 cost. No scheduler is active.</p></div><ShieldCheck/></div><div className="refresh-actions"><button onClick={()=>run.mutate('colorado_business_entities')} disabled={run.isPending}><RefreshCw/> Refresh Colorado</button><button onClick={()=>run.mutate('texas_active_franchise_taxpayers')} disabled={run.isPending}><RefreshCw/> Refresh Texas</button><span>Utah requires a separately delivered BEL file and cannot refresh dynamically.</span></div>{run.error&&<p className="error">{run.error.message}</p>}<RefreshHistory rows={data}/></section><section className="panel refresh-alerts"><div className="panel-title"><div><p className="eyebrow">Opt-in · in-app only</p><h2>Refresh issue alerts</h2><p>Notify me after a manual refresh fails or quarantines data. Alerts never run a refresh and never leave DealSage.</p></div><Bell/></div><div className="alert-subscriptions">{[['colorado_business_entities','Colorado'],['texas_active_franchise_taxpayers','Texas']].map(([key,name])=>{const active=subscriptions.some(item=>item.source_key===key&&item.active);return <button className={active?'active':''} key={key} onClick={()=>toggle(key)}>{active?<BellOff/>:<Bell/>}{active?`Disable ${name} alerts`:`Enable ${name} alerts`}</button>})}</div><AlertInbox alerts={alerts} onRead={id=>markRead.mutate(id)}/></section></>
}
