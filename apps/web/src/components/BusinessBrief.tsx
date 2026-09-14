import type {TransitionReviewItem} from './TransitionReview';
import './business-brief.css';

type Fact={label:string;value:string;evidence_id:number;publisher:string;url:string;classification:string};
export type LeadBrief={version:string;title:string;reported_names:string[];category:string;target_fit:string;
  signal:TransitionReviewItem|null;assessment_policy:{assessment_date:string;lookback_days:number}|null;
  timing:{route:string;event_date:string|null;announcement_date:string|null}|null;
  facts:Fact[];why_it_matters:string;next_gap:string;conflicts:string[];order:number};
const words=(value:string)=>value.replaceAll('_',' ');
export function sourceLink(value:string):string|undefined{
  try{const url=new URL(value);return ['http:','https:'].includes(url.protocol)&&!url.username&&!url.password?url.href:undefined;}catch{return undefined;}
}
function Citation({fact}:{fact:Fact}){
  const href=sourceLink(fact.url);
  return <small className="brief-citation">{words(fact.classification)} · {href?<a href={href} target="_blank" rel="noreferrer">{fact.publisher} · Evidence #{fact.evidence_id}</a>:<span>{fact.publisher} · Evidence #{fact.evidence_id}</span>}</small>;
}
export function BusinessBrief({brief,evidence}:{brief:LeadBrief;evidence:{id?:number;publisher:string;relevant_excerpt:string|null;canonical_url:string}[]}){
  const signal=brief.signal;
  const headline=signal?`${words(signal.signal_type)} · ${words(signal.event_status)}`:'Transition not yet identified';
  const date=brief.timing?.event_date||signal?.event_date;
  const locations=brief.facts.filter(f=>['Location','City','State'].includes(f.label));
  const context=brief.facts.filter(f=>['Industry','Activity','Company type'].includes(f.label));
  const financials=['Employees','Revenue','EBITDA'];
  const anchor=evidence.find(e=>e.id===signal?.evidence_id);
  const category=brief.category==='recent'?(brief.timing?.route==='planned_event'?'Future plan':brief.timing?.route==='recent_announcement'?'Recent announcement':'Recent signal'):brief.category==='background'?'Historical background':'Date needs review';
  return <div className="business-brief">
    <div className="brief-heading"><div><p className="eyebrow">{headline}</p><h3>{brief.title}</h3></div><span className={`brief-badge ${brief.category}`}>{category}</span></div>
    {brief.facts.filter(f=>f.label==='Business').map((f,i)=><p className="brief-names" key={i}>Source-reported business: {f.value}<Citation fact={f}/></p>)}
    <div className="brief-location">{locations.length?locations.map((f,i)=><span key={i}>{f.label}: <b>{f.value}</b><Citation fact={f}/></span>):<p>Location not yet reported</p>}</div>
    <p className="brief-date">{date?<>Event date: <b>{date.slice(0,10)}</b></>:brief.timing?.announcement_date?<>Announcement: <b>{brief.timing.announcement_date}</b> · event date unknown</>:<>Event date unknown</>}{signal?.person&&<> · {signal.person}</>}{brief.assessment_policy&&<small>Assessed {brief.assessment_policy.assessment_date} · {brief.assessment_policy.lookback_days}-day lookback</small>}</p>
    <p className="brief-relevance"><b>Why this merits attention</b><br/>{brief.why_it_matters}<small>DealSage research guidance · not an acquisition recommendation</small></p>
    {brief.target_fit==='conflicting'&&<p className="brief-conflict">Company identity or public/private status needs reconciliation.</p>}
    <div className="brief-context"><section><h4>Business context · source reports</h4>{context.length?context.map((f,i)=><p key={i}><b>{f.label}:</b> {f.value}<Citation fact={f}/></p>):<p>Activity and industry not yet reported.</p>}</section>
      <section><h4>Size and financial clues</h4>{financials.map(label=>{const rows=brief.facts.filter(f=>f.label===label);return <div key={label}>{rows.length?rows.map((f,i)=><p key={i}><b>{label}:</b> {f.value}<Citation fact={f}/></p>):<p><b>{label}:</b> Unknown</p>}</div>;})}</section></div>
    {anchor?.relevant_excerpt&&<details className="brief-source"><summary>Read the transition source · {anchor.publisher}</summary><blockquote>{anchor.relevant_excerpt}</blockquote>{sourceLink(anchor.canonical_url)&&<a href={sourceLink(anchor.canonical_url)} target="_blank" rel="noreferrer">Open retained source reference</a>}</details>}
    {brief.conflicts.length>0&&<section className="brief-conflict"><h4>Contradicting evidence · unresolved</h4>{brief.conflicts.map((c,i)=><p key={i}>{c}</p>)}</section>}
    <p className="brief-gap"><b>Next evidence gap</b><br/>{brief.next_gap}</p>
    <p className="brief-boundary">A reported role or transition does not establish ownership. Source assertions, model proposals and analyst decisions remain separate.</p>
  </div>;
}
