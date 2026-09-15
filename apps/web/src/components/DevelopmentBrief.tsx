import {useMutation, useQuery} from '@tanstack/react-query';
import {api, apiDownload} from '../api/client';

export type Contact = {source_id:number; recipient:string; channel:string; value:string; quote:string; public_business_use_reviewed:boolean};
export type Development = {summary:string; unknowns:string; readiness:string; readiness_reason:string; contact?:Contact};
export const emptyDevelopment:Development = {summary:'', unknowns:'', readiness:'not_ready', readiness_reason:''};
type Source = {id:number; publisher:string; relevant_excerpt:string};

export function DevelopmentForm({value, onChange, sources, disabled}:{value:Development; onChange:(v:Development)=>void; sources:Source[]; disabled:boolean}) {
  const edit = (v:Partial<Development>) => onChange({...value,...v});
  const contact = value.contact;
  const editContact = (v:Partial<Contact>) => edit({contact:{...contact!,...v}});
  const selected = sources.find(s=>s.id===contact?.source_id);
  return <fieldset className="development-form" disabled={disabled}><legend>Opportunity-development handoff</legend>
    <p>This is your purpose-specific assessment. Retain uncertainty; a transition does not establish that the business is for sale.</p>
    <label>Opportunity summary<textarea required minLength={10} maxLength={2000} value={value.summary} onChange={e=>edit({summary:e.target.value})}/></label>
    <label>Unknowns and limitations<textarea required minLength={10} maxLength={2000} value={value.unknowns} onChange={e=>edit({unknowns:e.target.value})}/></label>
    <label>Communication readiness<select value={value.readiness} onChange={e=>edit({readiness:e.target.value})}><option value="not_ready">Not ready</option><option value="reviewer_ready">Ready in my judgment</option></select></label>
    <label>Readiness rationale<textarea required minLength={10} maxLength={1000} value={value.readiness_reason} onChange={e=>edit({readiness_reason:e.target.value})}/></label>
    <label><input type="checkbox" checked={!!contact} disabled={!sources.length} onChange={e=>edit({contact:e.target.checked?{source_id:sources[0].id,recipient:'',channel:'website',value:'',quote:'',public_business_use_reviewed:false}:undefined})}/>Include a public business contact</label>
    <p>A missing contact remains unknown. Ready requires a reviewed contact; nothing is sent. Do not use a surviving relative as a sales contact based on an obituary.</p>
    {contact&&<>
      <label>Contact evidence<select value={contact.source_id} onChange={e=>editContact({source_id:Number(e.target.value),quote:'',value:'',public_business_use_reviewed:false})}>{sources.map(s=><option key={s.id} value={s.id}>Evidence {s.id} · {s.publisher}</option>)}</select></label>
      <blockquote>{selected?.relevant_excerpt||'No retained excerpt. Retrieve a permitted business-contact source and save a new brief before using it here.'}</blockquote>
      <label>Business recipient or team<input required minLength={2} maxLength={200} value={contact.recipient} onChange={e=>editContact({recipient:e.target.value})}/></label>
      <label>Business channel<select value={contact.channel} onChange={e=>editContact({channel:e.target.value})}><option value="website">Business website</option><option value="email">Public business email</option><option value="phone">Public business phone</option><option value="public_profile">Public business profile</option></select></label>
      <label>Contact value exactly as quoted<input required minLength={3} maxLength={500} value={contact.value} onChange={e=>editContact({value:e.target.value,public_business_use_reviewed:false})}/></label>
      <label>Exact contact quotation<textarea required minLength={5} maxLength={2000} value={contact.quote} onChange={e=>editContact({quote:e.target.value,public_business_use_reviewed:false})}/></label>
      <label><input type="checkbox" required checked={contact.public_business_use_reviewed} onChange={e=>editContact({public_business_use_reviewed:e.target.checked})}/>I reviewed this as a public business contact for the stated purpose, not a family contact inferred from an obituary.</label>
    </>}
  </fieldset>;
}

type Packet = {reviewer:string;reviewed_at:string;superseded_by_decision_id:number|null;boundaries:string;reviewer_decision:{development:Development};contact_provenance:{canonical_url:string;published_at:string|null;retrieved_at:string}|null;saved_brief:{version:number;content_hash:string}};
export function DevelopmentHandoff({caseId,decisionId,canExport}:{caseId:number;decisionId:number;canExport:boolean}) {
  const path=`/research/cases/${caseId}/decisions/${decisionId}/development-brief`;
  const packet=useQuery({queryKey:['development-brief',caseId,decisionId],queryFn:()=>api<Packet>(path)});
  const download=useMutation({mutationFn:()=>apiDownload(`${path}/export`,{},`dealsage-case-${caseId}-decision-${decisionId}.txt`)});
  if(packet.isLoading)return <p>Loading retained handoff…</p>;
  if(packet.isError)return <p role="alert">Handoff unavailable. <button onClick={()=>packet.refetch()}>Reload handoff</button></p>;
  if(!packet.data)return null;
  const p=packet.data,d=p.reviewer_decision.development,c=d.contact,s=p.contact_provenance;
  return <div className="investigation-item"><h4>Retained development brief</h4>
    {p.superseded_by_decision_id&&<p role="status">Historical handoff: superseded by decision {p.superseded_by_decision_id}. This is not the current reviewer decision.</p>}
    <p><b>Opportunity assessment:</b> {d.summary}</p><p><b>Unknowns and limitations:</b> {d.unknowns}</p>
    <p><b>Communication readiness:</b> {d.readiness==='reviewer_ready'?'Ready in reviewer judgment':'Not ready'} — {d.readiness_reason}</p>
    {c?<><p><b>Reviewer-selected contact:</b> {c.recipient} · {c.channel} · {c.value}</p><blockquote>{c.quote}</blockquote><p>Evidence {c.source_id} · {s?.canonical_url}</p><p>Published: {s?.published_at||'Unknown'} · Retrieved: {s?.retrieved_at||'Unknown'} · Reviewed: {p.reviewed_at} by {p.reviewer}</p></>:<p>Public business contact: unknown / not supplied.</p>}
    <p>{p.boundaries}</p><p>Based on saved brief version {p.saved_brief.version}. The export includes the frozen source, model and human records and their unresolved questions.</p>
    {canExport&&<button disabled={download.isPending} onClick={()=>download.mutate()}>Download reviewed handoff (.txt)</button>}
    {download.isSuccess&&<p role="status">Handoff download prepared.</p>}{download.error&&<p role="alert">{download.error.message}</p>}
  </div>;
}
