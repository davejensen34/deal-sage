import {useQuery} from '@tanstack/react-query';
import {AlertTriangle,Building2,CheckCircle2,Database,ExternalLink,UserRoundSearch} from 'lucide-react';
import {api} from '../api/client';
import {ResearchTrailView,Trail} from '../components/ResearchTrail';
import {SourceOperations,SourceSampleResult} from '../components/SourceOperations';
import {CaseNarratives,CaseNarrative} from '../components/CaseNarratives';

type Source={name:string;publisher:string;jurisdiction:string;landing_url:string;access_method:string;license:string;expected_refresh:string;role_value:string;limitations:string[]};
type Result={status:string;sample_size:number;selection:string;review_method:string;query_url:string;metrics:Record<string,number>;role_counts:Record<string,number>;recommendation:{decision:string;summary:string;next_step:string}};
type FunnelItem={stage:string;count:number};
type OriginMetrics={cases:number;evidence_items:number;claims:number;search_queries:number;research_steps:number};
const pct=(value:number)=>`${value}%`;

export function Research(){
  const sources=useQuery({queryKey:['research-sources'],queryFn:()=>api<Source[]>('/research/sources')});
  const result=useQuery({queryKey:['colorado-owner-experiment'],queryFn:()=>api<Result>('/research/experiments/colorado-owner-discovery')});
  const funnel=useQuery({queryKey:['research-funnel'],queryFn:()=>api<FunnelItem[]>('/research/funnel')});
  const trail=useQuery({queryKey:['research-trail-demo'],queryFn:()=>api<Trail>('/research/trails/1')});
  const sourceSamples=useQuery({queryKey:['milestone3-source-samples'],queryFn:()=>api<SourceSampleResult>('/research/experiments/milestone3-source-samples')});
  const cases=useQuery({queryKey:['research-case-narratives'],queryFn:()=>api<{cases:CaseNarrative[]}>('/research/case-narratives')});
  const caseMetrics=useQuery({queryKey:['research-case-metrics'],queryFn:()=>api<{origin_metrics:Record<string,OriginMetrics>}>('/research/case-metrics')});
  if(sources.isLoading||result.isLoading||funnel.isLoading||trail.isLoading||sourceSamples.isLoading)return <div className="loading">Loading research evidence…</div>;
  if(sources.isError||result.isError||funnel.isError||trail.isError||sourceSamples.isError||!sources.data?.[0]||!result.data||!funnel.data||!trail.data||!sourceSamples.data)return <div className="empty"><AlertTriangle/><h3>Research result unavailable</h3><p>The recorded experiment could not be loaded.</p></div>;
  const source=sources.data[0],data=result.data,metrics=data.metrics;
  return <>
    <div className="page-heading compact"><div><p className="eyebrow">Milestone 3.1 · evidence convergence</p><h1>Research workspace</h1><p>Follow signal-first, business-first, and hybrid research without mistaking evidence, inference, or scores for analyst judgment.</p></div><a href={data.query_url} target="_blank" rel="noreferrer"><ExternalLink/>Inspect Colorado query</a></div>
    <section className="research-verdict panel"><div className="verdict-icon"><AlertTriangle/></div><div><p className="eyebrow">Recommendation · {data.recommendation.decision}</p><h2>{data.recommendation.summary}</h2><p>{data.recommendation.next_step}</p></div></section>
    <section className="metric-grid research-metrics"><div className="metric"><Database/><span>Records retrieved</span><b>{data.sample_size}</b></div><div className="metric"><CheckCircle2/><span>Retrieval success</span><b>{pct(metrics.retrieval_success_percent)}</b></div><div className="metric"><Building2/><span>Agent evidence</span><b>{pct(metrics.registered_agent_evidence_percent)}</b></div><div className="metric danger"><UserRoundSearch/><span>Owner evidence</span><b>{pct(metrics.owner_controller_evidence_yield_percent)}</b></div><div className="metric"><Database/><span>Marginal API cost</span><b>${metrics.marginal_api_cost_usd}</b></div></section>
    <section className="panel funnel-panel"><div className="panel-title"><div><p className="eyebrow">Actual demo state</p><h2>Research funnel</h2><p>Counts reflect persisted validated stages; no expected conversions are invented.</p></div></div><div className="funnel-path">{funnel.data.map((item,index)=><div key={item.stage}><span>{index+1}</span><b>{item.count}</b><small>{item.stage.replaceAll('_',' ')}</small></div>)}</div></section>
    <ResearchTrailView trail={trail.data}/>
    <section className="panel origin-metrics"><div className="panel-title"><div><p className="eyebrow">Measured by entry strategy</p><h2>Convergence activity</h2><p>Observed persisted counts only; no conversion rate is projected.</p></div></div><div>{['signal_first','business_first','hybrid'].map(origin=>{const metric=caseMetrics.data?.origin_metrics[origin];return <article key={origin}><b>{origin.replaceAll('_',' ')}</b><strong>{metric?.cases||0} cases</strong><small>{metric?.evidence_items||0} evidence · {metric?.claims||0} claims · {metric?.research_steps||0} steps</small></article>})}</div></section>
    <CaseNarratives cases={cases.data?.cases||[]}/>
    <SourceOperations result={sourceSamples.data}/>
    <div className="research-grid">
      <section className="panel"><div className="panel-title"><div><h2>Role classification</h2><p>Observed source roles, never inferred ownership.</p></div><span>{data.status}</span></div><div className="role-list">{Object.entries(data.role_counts).map(([role,count])=><div key={role}><span>{role.replaceAll('_',' ')}</span><b>{count}</b></div>)}</div><div className="research-rule"><AlertTriangle/><p><b>Registered agent ≠ owner.</b> A natural-person name or shared address does not change the filed role.</p></div></section>
      <section className="panel source-card"><div className="panel-title"><div><h2>{source.name}</h2><p>{source.publisher}</p></div><span>{source.jurisdiction}</span></div><dl><dt>Access</dt><dd>{source.access_method}</dd><dt>License</dt><dd>{source.license}</dd><dt>Refresh</dt><dd>{source.expected_refresh}</dd><dt>Relationship value</dt><dd>{source.role_value}</dd></dl><a href={source.landing_url} target="_blank" rel="noreferrer">Open official dataset <ExternalLink/></a></section>
      <section className="panel method-card"><h2>Experiment method</h2><p>{data.selection}</p><p>{data.review_method}</p><p className="muted">Latency: {metrics.retrieval_latency_ms} ms · Name coverage: {pct(metrics.entity_name_coverage_percent)} · Formation-date coverage: {pct(metrics.formation_date_coverage_percent)}</p></section>
      <section className="panel method-card"><h2>Known source limits</h2>{source.limitations.map(limit=><p key={limit}><CheckCircle2/>{limit}</p>)}</section>
    </div>
  </>;
}
