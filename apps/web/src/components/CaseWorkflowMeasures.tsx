import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {Link} from 'react-router-dom';
import {api} from '../api/client';
import '../pages/discovery.css';

type Purpose={purpose:string;decisions:number;useful:number;not_useful:number;missing_judgments:number;assessed:number;useful_percent:number|null;timed_reviews:number;median_review_seconds:number|null};
type Measures={cost_coverage?:{boundary:string;rows:{name:string;records:number;recorded_amount:number|null;unit:string;missing_cost_records:number;scope:string}[]};total_cases:number;cases_with_decisions:number;cases_without_decisions:number;decisions:Record<string,number>;purposes:Purpose[];reservations:{kind:string;attempts:number;reserved_cents:number;outcomes:Record<string,number>}[];items:{id:number;case_id:number;actor:string;created_at:string;decision:{brief_version:number;purpose:string;outcome:string;feedback?:{usefulness:string;reason:string;review_seconds?:number}}}[];has_next:boolean;measurement_scope:string;cost_scope:string};
const words=(s:string)=>s.replaceAll('_',' ');
export function CaseWorkflowMeasures(){
  const [page,setPage]=useState(1);
  const query=useQuery({queryKey:['case-workflow-measures',page],queryFn:()=>api<Measures>(`/research/case-workflow-measures?page=${page}`)});
  const d=query.data;
  return <section className="panel case-measures"><h2>Case review measures</h2><p>Source reports, model interpretations and reviewer usefulness are different measures. These workspace counts do not establish representative precision or pass a human evaluation cohort.</p>
    {query.isError?<p role="alert">Case review measures unavailable. <button onClick={()=>query.refetch()}>Retry measures</button></p>:query.isLoading?<p>Loading case measures…</p>:d&&<>
      <p>{d.measurement_scope}</p><p><b>{d.total_cases} cases</b> · {d.cases_with_decisions} with a decision · {d.cases_without_decisions} without a decision</p>
      {!d.total_cases&&<p>No research cases yet. Start with Discover; missing judgments are never counted as useful.</p>}
      <p>Current decisions: {Object.entries(d.decisions).map(([key,n])=>`${words(key)}: ${n}`).join(' · ')||'None recorded'}</p>
      <div className="case-measures-grid">{d.purposes.map(p=><article key={p.purpose}><h3>{words(p.purpose)}</h3><p>{p.useful} useful / {p.assessed} assessed{p.useful_percent===null?' · Not measured':` · ${p.useful_percent}% of assessed`} · {p.not_useful} not useful</p><p>{p.missing_judgments} missing usefulness judgments among {p.decisions} current decisions</p><p>Median self-reported review time: {p.median_review_seconds===null?'Not measured':`${p.median_review_seconds} seconds`} ({p.timed_reviews} timed reviews). Latest decisions only; not cumulative effort or time saved.</p></article>)}</div>
      <h3>Research reservations</h3><p>{d.cost_scope}</p>{d.reservations.map(r=><p key={r.kind}>{words(r.kind)}: {r.reserved_cents} USD cents reserved across {r.attempts} attempts · {Object.entries(r.outcomes).map(([s,n])=>`${words(s)}: ${n}`).join(', ')||'No attempts'}</p>)}
      {d.cost_coverage&&<><h3>Cost coverage and unknowns</h3><p>{d.cost_coverage.boundary}</p>{d.cost_coverage.rows.map(r=><details key={r.name}><summary>{r.name}: {r.records} records · {r.missing_cost_records} with missing or incomplete cost data</summary><p>Recorded ledger amount: {r.recorded_amount===null?'Unknown / not recorded':`${r.recorded_amount} ${r.unit}`}.</p><p>{r.scope}</p></details>)}</>}
      <h3>Latest attributable decisions</h3>{!d.items.length&&<p>No decisions on this page.</p>}{d.items.map(r=><article key={r.id}><Link to={`/research/cases/${r.case_id}`}>Case {r.case_id} · {words(r.decision.outcome)}</Link><p>{r.actor} · {new Date(r.created_at).toLocaleString()} · brief version {r.decision.brief_version} · {words(r.decision.purpose)}</p><p>{words(r.decision.feedback?.usefulness||'not_assessed')}{r.decision.feedback?.reason&&<> — {r.decision.feedback.reason}</>} · Review time: {r.decision.feedback?.review_seconds===undefined?'Not recorded':`${r.decision.feedback.review_seconds} seconds`}</p></article>)}
      <nav aria-label="Case measure pages"><button disabled={page===1} onClick={()=>setPage(page-1)}>Previous reviews</button> Page {page} <button disabled={!d.has_next} onClick={()=>setPage(page+1)}>Next reviews</button></nav>
    </>}
  </section>;
}
