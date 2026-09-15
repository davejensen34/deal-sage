import {CaseInvestigation} from '../components/CaseInvestigation';
import {useQuery} from '@tanstack/react-query';
import {Link, useParams, useSearchParams} from 'react-router-dom';
import {api} from '../api/client';
import {CaseNarrative, CaseNarratives} from '../components/CaseNarratives';
import './reviewer-inbox.css';

const words = (value: string) => value.replaceAll('_', ' ');
const signals = ['possible_death','retirement','succession','ownership_change','founder_exit','dissolution','restructuring','leadership_change'];
type InboxCase = CaseNarrative & {candidate_match_id: number|null; linked_business: {id:number;name:string;state:string|null}|null};
type InboxPage = {cases:InboxCase[];total:number;page:number;page_size:number};

export function ReviewerInbox() {
  const [params, setParams] = useSearchParams();
  const page = Math.max(1, Number(params.get('page')) || 1);
  const query = new URLSearchParams({page:String(page),page_size:'10'});
  for (const key of ['state','signal','since','until','date_basis']) if (params.get(key)) query.set(key, params.get(key)!);
  const result = useQuery({queryKey:['reviewer-inbox',query.toString()],queryFn:()=>api<InboxPage>(`/research/inbox?${query}`)});
  const change = (key:string,value:string) => {
    const next = new URLSearchParams(params);
    value ? next.set(key,value) : next.delete(key);
    if (key !== 'page') next.delete('page');
    setParams(next);
  };
  return <div className="reviewer-workbench">
    <div className="page-heading"><div><p className="eyebrow">Reviewer workbench</p><h1>Review business transitions</h1><p>Start with what changed. Decide which evidence deserves a closer look.</p></div><Link className="primary" to="/discover">Find transitions</Link></div>
    <form className="inbox-filters" onSubmit={e=>e.preventDefault()} aria-label="Filter research cases">
      <label>State<select value={params.get('state')||''} onChange={e=>change('state',e.target.value)}><option value="">All states / unknown</option>{['CO','UT','TX'].map(s=><option key={s}>{s}</option>)}</select></label>
      <label>Transition<select value={params.get('signal')||''} onChange={e=>change('signal',e.target.value)}><option value="">All signals / unknown</option>{signals.map(s=><option key={s} value={s}>{words(s)}</option>)}</select></label>
      <label>Date basis<select value={params.get('date_basis')||'event'} onChange={e=>change('date_basis',e.target.value)}><option value="event">Reported event date</option><option value="announcement">Source publication date</option></select></label>
      <label>On or after<input type="date" value={params.get('since')||''} onChange={e=>change('since',e.target.value)}/></label>
      <label>On or before<input type="date" value={params.get('until')||''} onChange={e=>change('until',e.target.value)}/></label>
      <button type="button" onClick={()=>setParams({})}>Clear filters</button>
    </form>
    <p className="inbox-explainer">Dates filter retained assertions; they do not verify an event or its business relevance. Undated leads remain visible without date filters. State includes linked entities and source-reported geography.</p>
    {result.isLoading ? <p role="status">Loading research cases…</p> : result.isError ? <section className="panel" role="alert"><h2>Research cases are unavailable</h2><p>{result.error.message}</p><button onClick={()=>result.refetch()}>Try again</button></section> : result.data && <>
      <p role="status">{result.data.total} research cases · newest case updates first</p>
      {!result.data.cases.length ? <section className="panel inbox-empty"><h2>{result.data.total ? 'No cases on this page' : 'No research cases match'}</h2><p>Unresolved business names are welcome here. Clear filters to see other retained research.</p><p>Start bounded discovery from an event, a business or a market. Existing source refreshes remain available in Sources & research.</p><Link to="/candidates">Review existing candidates</Link></section> : <div className="inbox-cards">{result.data.cases.map(c=><article className="panel inbox-card" key={c.id}>
        <p className="eyebrow">Case {c.id} · {words(c.origin_strategy)}</p><h2><Link to={`/research/cases/${c.id}`}>{c.lead_brief?.title||'Business not yet identified'}</Link></h2>
        <p>{c.linked_business ? `Linked entity: ${c.linked_business.name} · ${c.linked_business.state||'State unknown'}` : 'Business identity not linked to an entity'}</p>
        <div className="inbox-signals">{c.transitions?.filter(t=>t.claim_status==='asserted').length ? c.transitions.filter(t=>t.claim_status==='asserted').map(t=><p key={t.claim_id}><b>{words(t.signal_type)} · {words(t.event_status)}</b><br/>Event: {t.event_date||'unknown'} · Publication: {t.publication_date?.slice(0,10)||'unknown'}<br/><small>Source assertion · {t.publisher} · Claim #{t.claim_id}</small></p>) : <p>Transition and event date not yet established.</p>}</div>
        <p className="inbox-question"><b>Next evidence question</b><br/>{c.lead_brief?.next_gap||'Identify the business and transition from retained evidence.'}</p>
        <p>Research: {words(c.stop_reason||c.status)}</p>
        <p>{c.conclusion ? `Reviewer: ${c.conclusion.analyst} · ${words(c.conclusion.outcome)} (${c.conclusion.status})` : 'No reviewer conclusion recorded'}</p>
        <div className="inbox-links"><Link to={`/research/cases/${c.id}`}>Open research brief →</Link>{c.candidate_match_id && <Link to={`/candidates/${c.candidate_match_id}`}>Linked candidate</Link>}</div>
      </article>)}</div>}
      <nav className="pagination" aria-label="Research case pages"><button disabled={page===1} onClick={()=>change('page',String(page-1))}>Previous</button><span>Page {page} of {Math.max(1,Math.ceil(result.data.total/10))}</span><button disabled={page*10>=result.data.total} onClick={()=>change('page',String(page+1))}>Next</button></nav>
    </>}
  </div>;
}

export function ResearchCaseDetail() {
  const {id} = useParams();
  const result = useQuery({queryKey:['research-case',id],queryFn:()=>api<InboxCase>(`/research/cases/${id}`),retry:false});
  return <><Link className="back" to="/">← Back to reviewer inbox</Link>
    {result.isLoading ? <p role="status">Loading research brief…</p> : result.isError ? <section className="panel" role="alert"><h1>Research brief unavailable</h1><p>{result.error.message}</p><button onClick={()=>result.refetch()}>Try again</button></section> : result.data && <>
      {result.data.linked_business && <p>Linked entity: {result.data.linked_business.name}. Source-reported alternatives remain in the brief.</p>}
      {result.data.candidate_match_id && <p><Link to={`/candidates/${result.data.candidate_match_id}`}>Open linked review candidate</Link></p>}
      <CaseNarratives cases={[result.data]}/>
      <CaseInvestigation key={result.data.id} caseId={result.data.id}/>
    </>}
  </>;
}
