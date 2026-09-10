import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {AlertTriangle,CheckCircle2,Clock3,RefreshCw,ShieldCheck} from 'lucide-react';
import {api} from '../api/client';
import {fmt} from './Status';
import '../source-refresh.css';

export type SourceRefresh={id:number;source_key:string;jurisdiction:string;requested_by:string;status:string;record_limit:number;approved_cost_usd:number;actual_cost_usd:number;freshness_status:string;freshness_reason?:string;error_code?:string;started_at:string;finished_at?:string;result_summary:Record<string,any>};

const label=(value:string)=>value.replaceAll('_',' ');

export function RefreshHistory({rows}:{rows:SourceRefresh[]}){
  if(!rows.length)return <p className="muted">No analyst-initiated refresh has run yet.</p>;
  return <div className="refresh-history">{rows.map(row=><article key={row.id}><div className={`refresh-state ${row.status}`}>{row.status==='succeeded'?<CheckCircle2/>:row.status==='failed'?<AlertTriangle/>:<Clock3/>}</div><div><b>{row.jurisdiction} · {label(row.status)}</b><span>{row.requested_by} · {row.record_limit} record limit · {fmt(row.started_at)}</span><small>{label(row.freshness_status)}{row.freshness_reason&&` — ${row.freshness_reason}`}</small></div><dl><dt>Retrieved</dt><dd>{row.result_summary.retrieved??'—'}</dd><dt>Curated</dt><dd>{row.result_summary.curated??'—'}</dd><dt>Cost</dt><dd>${row.actual_cost_usd.toFixed(2)}</dd></dl></article>)}</div>
}

export function SourceRefreshes(){
  const qc=useQueryClient();
  const {data=[]}=useQuery({queryKey:['source-refreshes'],queryFn:()=>api<SourceRefresh[]>('/research/source-refreshes')});
  const run=useMutation({mutationFn:(source_key:string)=>api('/research/source-refreshes',{method:'POST',body:JSON.stringify({source_key,record_limit:25,approved_cost_usd:0})}),onSuccess:()=>qc.invalidateQueries({queryKey:['source-refreshes']})});
  return <section className="panel source-refreshes"><div className="panel-title"><div><p className="eyebrow">Milestone 5 · explicit refresh</p><h2>Bounded source refresh</h2><p>Each run is analyst-initiated, limited to 25 records, and approved for $0 cost. No scheduler is active.</p></div><ShieldCheck/></div><div className="refresh-actions"><button onClick={()=>run.mutate('colorado_business_entities')} disabled={run.isPending}><RefreshCw/> Refresh Colorado</button><button onClick={()=>run.mutate('texas_active_franchise_taxpayers')} disabled={run.isPending}><RefreshCw/> Refresh Texas</button><span>Utah requires a separately delivered BEL file and cannot refresh dynamically.</span></div>{run.error&&<p className="error">{run.error.message}</p>}<RefreshHistory rows={data}/></section>
}
