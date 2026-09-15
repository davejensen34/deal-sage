import {useState} from 'react';
import {useMutation} from '@tanstack/react-query';
import {api} from '../api/client';
import '../pages/discovery.css';

type Change={id:number;kind:string;fields:string[];before:unknown;after:unknown};
type Group={counts:{added:number;changed:number;removed:number};rows:Change[]};
type Version={version:number;actor:string;created_at:string;content_hash:string};
type Comparison={from:Version;to:Version;unchanged:boolean;groups:Record<string,Group>;context_changes:{field:string;before:unknown;after:unknown}[]};
const labels:Record<string,string>={sources:'Source reports and provenance',claim_records:'Claim fingerprints',model_observations:'Model interpretations',reviews:'Human model reviews',conclusions:'Human evidence conclusions',questions:'Research questions',conflicts:'Recorded conflicts',source_brief:'Business, timing and fit guidance',transitions:'Retained transition assertions',case_status:'Research execution status',model_scope:'Model inclusion scope'};
const name=(s:string)=>labels[s]||s.replaceAll('_',' ');
function BeforeAfter({before,after}:{before:unknown;after:unknown}) {
  return <div className="brief-comparison-values"><div><h5>Earlier saved value</h5><pre>{before===null?'Not present / unknown':JSON.stringify(before,null,2)}</pre></div><div><h5>Later saved value</h5><pre>{after===null?'Not present / unknown':JSON.stringify(after,null,2)}</pre></div></div>;
}
function RecordGroup({group,value}:{group:string;value:Group}) {
  const [page,setPage]=useState(1),c=value.counts;
  return <details><summary>{name(group)}: {c.added} added · {c.changed} changed · {c.removed} removed</summary>
    {!value.rows.length&&<p>No retained-record differences in this category.</p>}
    {value.rows.slice((page-1)*10,page*10).map(r=><article className="investigation-item" key={r.id}><h4>{name(group)} · record {r.id} · {r.kind}</h4><p>Fields: {r.fields.join(', ')}</p><BeforeAfter before={r.before} after={r.after}/></article>)}
    {value.rows.length>10&&<nav aria-label={`${name(group)} comparison pages`}><button disabled={page===1} onClick={()=>setPage(page-1)}>Previous changes</button> Page {page} <button disabled={page*10>=value.rows.length} onClick={()=>setPage(page+1)}>Next changes</button></nav>}
  </details>;
}

export function BriefComparison({caseId}:{caseId:number}) {
  const [from,setFrom]=useState(1),[to,setTo]=useState(1);
  const comparison=useMutation({mutationFn:()=>api<Comparison>(`/research/cases/${caseId}/brief-comparison?from_version=${from}&to_version=${to}`)});
  const valid=Number.isInteger(from)&&Number.isInteger(to)&&from>=1&&to>=from;
  const result=comparison.data;
  return <section className="brief-comparison"><h3>Compare saved brief versions</h3>
    <p>After an explicit follow-up, permitted retrieval or extraction, preview and save a new brief above. Compare its version with an earlier saved version here. This comparison does not search or refresh external sources, record a completed review, or change your monitoring date.</p>
    <form className="discovery-form" onSubmit={e=>{e.preventDefault();if(valid)comparison.mutate()}}>
      <div className="discovery-limits"><label>Earlier saved version<input type="number" required min={1} step={1} value={from} disabled={comparison.isPending} onChange={e=>{setFrom(Number(e.target.value));comparison.reset()}}/></label>
        <label>Later saved version<input type="number" required min={from||1} step={1} value={to} disabled={comparison.isPending} onChange={e=>{setTo(Number(e.target.value));comparison.reset()}}/></label></div>
      {!valid&&<p role="alert">Choose positive versions with the earlier version first.</p>}
      <button disabled={!valid||comparison.isPending}>{comparison.isPending?'Comparing…':'Compare these versions'}</button>
    </form>
    {comparison.error&&<p role="alert">{comparison.error.message}</p>}
    {result&&<div><h4>Saved version {result.from.version} → saved version {result.to.version}</h4>
      <p>{result.unchanged?'No differences between these saved snapshots.':'Retained records or case context differ. Inspect the changes below.'}</p>
      <p>Changes do not prove a new transition, independent corroboration, ownership or sale intent. Materiality is a reviewer judgment. Removed means absent from the later snapshot, not false or retracted. Claim fingerprints expose changed records, not a semantic interpretation.</p>
      {[['Earlier',result.from],['Later',result.to]].map(([label,v])=>{const version=v as Version;return <p key={label as string}>{label as string}: {version.actor} · {new Date(version.created_at).toLocaleString()} · SHA-256 <code>{version.content_hash}</code></p>})}
      <h4>Case context changes</h4>{!result.context_changes.length&&<p>No case-level differences.</p>}
      {result.context_changes.map(c=><details key={c.field}><summary>{name(c.field)}</summary><BeforeAfter before={c.before} after={c.after}/></details>)}
      <h4>Source, model and human records</h4>{Object.entries(result.groups).map(([group,value])=><RecordGroup key={`${result.from.version}-${result.to.version}-${group}`} group={group} value={value}/>)}
    </div>}
  </section>;
}
