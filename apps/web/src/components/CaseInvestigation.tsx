import {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {api} from '../api/client';
import {useIdentity} from './AuthGate';
import './case-investigation.css';
import {RetrieveSource,RetrievalHistory} from './CaseRetrieval';
import {ExtractEvidence,ExtractionHistory} from './CaseExtraction';

type Page<T>={items:T[];has_next:boolean};
type Source={id:number;url:string;publisher:string;source_type:string;access:string;reason:string|null;reviewer:string|null;reviewed_at:string|null;blocking_observations:string[]};
type Evidence={id:number;url:string;publisher:string;classification:string;source_type:string;published_at:string|null;retrieved_at:string;content_hash:string;artifact_id:number|null;excerpt:string;excerpt_truncated:boolean};
type Claim={id:number;subject:string;predicate:string;value:unknown;relationship:string|null;classification:string;status:string;authority:string;directness:string};
type Comparison={evidence_id:number;publisher:string;url:string;relationship:string;rule:string;explanation:string};
const words=(s:string)=>s.replaceAll('_',' ');
const date=(s:string|null)=>s?new Date(s).toLocaleString():'Not reported';

function SourceLink({url}:{url:string}) {
  try { const parsed=new URL(url); if(['http:','https:'].includes(parsed.protocol))return <a href={url} target="_blank" rel="noreferrer">Open source website</a>; } catch { /* Imported evidence may lack a usable public URL. */ }
  return <span>Source URL unavailable</span>;
}

function Pages({page,next,setPage,label}:{page:number;next:boolean;setPage:(n:number)=>void;label:string}) {
  return <nav aria-label={`${label} pages`}><button disabled={page===1} onClick={()=>setPage(page-1)}>Previous {label}</button><span> Page {page} </span><button disabled={!next} onClick={()=>setPage(page+1)}>Next {label}</button></nav>;
}

function AccessReview({source,caseId}:{source:Source;caseId:number}) {
  const identity=useIdentity(),qc=useQueryClient();
  const [decision,setDecision]=useState('blocked'),[reason,setReason]=useState(''),[reviewed,setReviewed]=useState(false);
  const save=useMutation({mutationFn:()=>api(`/research/cases/${caseId}/investigation/sources/${source.id}/access`,{method:'POST',body:JSON.stringify({decision,reason,reviewed_conditions:reviewed})}),onSuccess:()=>{
    qc.invalidateQueries({queryKey:['case-investigation',caseId]});qc.invalidateQueries({queryKey:['research-case']});qc.invalidateQueries({queryKey:['research-case-narratives']});
  }});
  const canReview=!!identity&&identity.role!=='viewer';
  return <article className="investigation-item"><h3>{source.publisher} · source {source.id}</h3><SourceLink url={source.url}/><p>Provider-reported {words(source.source_type)} · Access: <b>{source.access}</b></p>
    {!!source.blocking_observations.length&&<p>Recorded restrictions: {source.blocking_observations.map(words).join(', ')}. Approval is unavailable; the clue remains useful.</p>}
    {source.access!=='pending'?<p>Reviewed by {source.reviewer||'not recorded'} · {date(source.reviewed_at)}<br/>Rationale: {source.reason||'not recorded'}. This access decision is retained and cannot be overwritten.</p>:canReview?<form onSubmit={e=>{e.preventDefault();save.mutate()}}>
      <label>Access decision<select value={decision} onChange={e=>setDecision(e.target.value)}><option value="blocked">Block retrieval</option><option value="approved" disabled={!!source.blocking_observations.length}>Approve later bounded retrieval</option></select></label>
      <label>Access rationale<textarea required minLength={5} maxLength={1000} value={reason} onChange={e=>setReason(e.target.value)} placeholder="Explain the access conditions you reviewed or why retrieval should be blocked."/></label>
      {decision==='approved'&&<label className="investigation-check"><input type="checkbox" checked={reviewed} onChange={e=>setReviewed(e.target.checked)}/>I reviewed the source's access conditions and found no authentication, paywall, CAPTCHA, robots or reuse restriction preventing this bounded retrieval.</label>}
      <p>Approval records access permission only. It does not verify a claim, approve spending or retrieve a page.</p>
      <button disabled={save.isPending||reason.trim().length<5||(decision==='approved'&&(!reviewed||!!source.blocking_observations.length))}>Record access decision</button>
      {save.error&&<p role="alert">{save.error.message} <button type="button" onClick={()=>qc.invalidateQueries({queryKey:['case-investigation',caseId]})}>Reload source decisions</button></p>}
    </form>:<p>An analyst is required to record an access decision.</p>}
    {source.access==='approved'&&<RetrieveSource caseId={caseId} sourceId={source.id} url={source.url}/>}
  </article>;
}

function Claims({caseId,evidenceId}:{caseId:number;evidenceId:number}) {
  const [page,setPage]=useState(1);
  const result=useQuery({queryKey:['case-investigation',caseId,'claims',evidenceId,page],queryFn:()=>api<Page<Claim>>(`/research/cases/${caseId}/investigation/evidence/${evidenceId}/claims?page=${page}`)});
  return <section><h4>Retained claims</h4>{result.isLoading?<p>Loading claims…</p>:result.isError?<p role="alert">Claims unavailable. <button onClick={()=>result.refetch()}>Try again</button></p>:<>
    {!result.data?.items.length&&<p>No claims extracted from this evidence yet.</p>}
    {result.data?.items.map(c=><article key={c.id}><p><b>Claim {c.id} · {words(c.predicate)}</b> · {words(c.classification)} · {words(c.status)}</p><pre>{JSON.stringify(c.value,null,2)}</pre><p>Subject: {words(c.subject)} · Relationship: {c.relationship?words(c.relationship):'not asserted'} · Authority: {words(c.authority)} · Directness: {words(c.directness)}</p></article>)}
    <Pages label="claims" page={page} next={!!result.data?.has_next} setPage={setPage}/>
  </>}</section>;
}

function EvidenceItem({item,caseId}:{item:Evidence;caseId:number}) {
  const [expanded,setExpanded]=useState(false);
  const [comparing,setComparing]=useState(false);
  return <article className="investigation-item"><h3>Evidence {item.id} · {item.publisher}</h3><SourceLink url={item.url}/><p>{words(item.classification)} · {words(item.source_type)}</p>
    <p>Published (UTC date): {item.published_at?.slice(0,10)||'Not reported'}<br/>Retrieved: {date(item.retrieved_at)}</p>
    <p>Publication and retrieval dates do not establish the transition event date. Repeated coverage does not prove independent corroboration.</p>
    <details><summary>Retained excerpt and provenance</summary><blockquote>{item.excerpt||'No excerpt retained.'}</blockquote>{item.excerpt_truncated&&<p>Excerpt display limited to 2,000 characters.</p>}<p>SHA-256: <code>{item.content_hash}</code><br/>Raw artifact: {item.artifact_id?`#${item.artifact_id}`:'Not linked; legacy or manually supplied evidence'}</p></details>
    <button aria-expanded={expanded} onClick={()=>setExpanded(!expanded)}>{expanded?'Hide':'Inspect'} claims for evidence {item.id}</button>{expanded&&<Claims caseId={caseId} evidenceId={item.id}/>}
    <button aria-expanded={comparing} onClick={()=>setComparing(!comparing)}>{comparing?'Hide':'Compare'} source independence for evidence {item.id}</button>{comparing&&<Comparisons caseId={caseId} evidenceId={item.id}/>}
    <ExtractEvidence caseId={caseId} evidenceId={item.id}/>
  </article>;
}

function Comparisons({caseId,evidenceId}:{caseId:number;evidenceId:number}) {
  const [page,setPage]=useState(1);
  const result=useQuery({queryKey:['case-investigation',caseId,'comparisons',evidenceId,page],queryFn:()=>api<Page<Comparison>>(`/research/cases/${caseId}/investigation/evidence/${evidenceId}/comparisons?page=${page}`)});
  const labels:Record<string,string>={duplicate:'Duplicate content',syndicated:'Shared original story',same_publisher:'Same recorded publisher',independent:'No shared provenance observed',unknown:'Independence unknown'};
  return <section aria-label={`Source independence for evidence ${evidenceId}`}><h4>Source independence</h4>
    <p>Deterministic comparison of retained provenance, not a human verification. Multiple websites may repeat one account. These comparisons do not establish truth, ownership or sale intent, and do not change scores.</p>
    {result.isLoading?<p>Loading comparisons…</p>:result.isError?<p role="alert">Comparisons unavailable. <button onClick={()=>result.refetch()}>Try again</button></p>:<>
      {!result.data?.items.length&&<p>{page===1?"No other retained evidence to compare in this case. Independence is unknown.":"No comparisons on this page. Return to the previous page."}</p>}
      {result.data?.items.map(row=><article key={row.evidence_id}><h4>Compared with evidence {row.evidence_id} · {row.publisher||'Publisher not recorded'}</h4><SourceLink url={row.url}/><p><b>{labels[row.relationship]||'Independence unknown'}</b></p><p>{row.explanation}</p></article>)}
      <Pages label={`comparisons for evidence ${evidenceId}`} page={page} next={!!result.data?.has_next} setPage={setPage}/>
    </>}
  </section>;
}

export function CaseInvestigation({caseId}:{caseId:number}) {
  const [sourcePage,setSourcePage]=useState(1),[evidencePage,setEvidencePage]=useState(1);
  const sources=useQuery({queryKey:['case-investigation',caseId,'sources',sourcePage],queryFn:()=>api<Page<Source>>(`/research/cases/${caseId}/investigation/sources?page=${sourcePage}`)});
  const evidence=useQuery({queryKey:['case-investigation',caseId,'evidence',evidencePage],queryFn:()=>api<Page<Evidence>>(`/research/cases/${caseId}/investigation/evidence?page=${evidencePage}`)});
  return <section className="panel case-investigation"><h2>Investigate sources and evidence</h2><p>Review access separately from what a source claims. Search clues, retained source material, model interpretations and human decisions remain distinct.</p>
    <h3>Source-access review</h3>{sources.isLoading?<p>Loading sources…</p>:sources.isError?<p role="alert">Sources unavailable. <button onClick={()=>sources.refetch()}>Try again</button></p>:<>
      {!sources.data?.items.length&&<p>No discovered sources in this case yet.</p>}{sources.data?.items.map(s=><AccessReview key={s.id} source={s} caseId={caseId}/>)}<Pages label="sources" page={sourcePage} next={!!sources.data?.has_next} setPage={setSourcePage}/>
    </>}
    <h3>Retained source evidence</h3>{evidence.isLoading?<p>Loading evidence…</p>:evidence.isError?<p role="alert">Evidence unavailable. <button onClick={()=>evidence.refetch()}>Try again</button></p>:<>
      {!evidence.data?.items.length&&<p>No source documents retained yet. An operator can retrieve an access-approved source using the bounded controls above. Extraction and analysis follow separately.</p>}{evidence.data?.items.map(e=><EvidenceItem key={e.id} item={e} caseId={caseId}/>)}<Pages label="evidence" page={evidencePage} next={!!evidence.data?.has_next} setPage={setEvidencePage}/>
    </>}
    <RetrievalHistory caseId={caseId}/>
    <ExtractionHistory caseId={caseId}/>
  </section>;
}
