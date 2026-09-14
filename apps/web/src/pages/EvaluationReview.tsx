import {useRef,useState} from 'react';
import {feedbackRecord,MAX_PACKAGE_BYTES,parseReviewPackage,safeSourceUrl,type Feedback,type ReviewPackage} from '../evaluationReview';
import '../evaluation-review.css';

const label=(s:string)=>s.replaceAll('_',' ');
const blank=():Feedback=>({usefulness:'',rationale:'',review_minutes:''});
export function EvaluationReview(){
  const [loaded,setLoaded]=useState<{data:ReviewPackage;hash:string}|null>(null);
  const [reviewer,setReviewer]=useState('');
  const [feedback,setFeedback]=useState<Record<string,Feedback>>({});
  const [error,setError]=useState('');
  const [notice,setNotice]=useState('');
  const [loading,setLoading]=useState(false);
  const generation=useRef(0);
  async function load(file:File){
    const version=++generation.current;
    setLoading(true);setLoaded(null);setFeedback({});setError('');setNotice('');
    try{
      if(file.size>MAX_PACKAGE_BYTES)throw new Error('Package exceeds the 2 MB limit.');
      const bytes=await file.arrayBuffer();
      const data=parseReviewPackage(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
      const digest=await crypto.subtle.digest('SHA-256',bytes);
      const hash=Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
      if(generation.current===version)setLoaded({data,hash});
    }catch(reason){if(generation.current===version)setError(reason instanceof Error?reason.message:'Unable to read package.')}
    finally{if(generation.current===version)setLoading(false)}
  }
  function update(slot:string,changes:Partial<Feedback>){setFeedback(old=>({...old,[slot]:{...(old[slot]||blank()),...changes}}));setNotice('')}
  function download(){
    if(!loaded)return;
    setError('');setNotice('');
    try{
      const record=feedbackRecord(loaded.data,loaded.hash,reviewer,feedback);
      const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)],{type:'application/json'}));
      const link=document.createElement('a');link.href=url;link.download=`dealsage-evaluation-feedback-${loaded.hash.slice(0,12)}.json`;
      document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
      setNotice('Feedback download requested. Keep the file with the review package; it has not been saved to DealSage.');
    }catch(reason){setError(reason instanceof Error?reason.message:'Unable to export feedback.')}
  }
  return <div className="evaluation-review">
    <div className="page-heading"><div><p className="eyebrow">Analyst evaluation</p><h1>Is this research useful?</h1><p>Compare retained evidence, model observations and contextual guidance before recording your own judgment.</p></div></div>
    <section className="panel evaluation-import"><h2>Open a review package</h2><p>Select a locally prepared evaluation package. Its contents stay in this browser; no research runs and no cases change. Unsaved feedback is lost when you leave or load another package.</p>
      <label>Review package (.json)<input type="file" accept=".json,application/json" onChange={e=>{const file=e.target.files?.[0];if(file)void load(file);e.target.value=''}}/></label>
      {loading&&<p role="status">Reading local package…</p>}
    </section>
    {error&&<p role="alert" className="form-error">{error}</p>}
    {loaded&&<>
      <section className="panel evaluation-provenance"><b>{loaded.data.items.length} packets loaded</b><p>The package fingerprint binds your feedback to this file. It does not verify source truth or package authorship.</p><details><summary>Package provenance</summary><dl><dt>Selected file SHA-256</dt><dd>{loaded.hash}</dd><dt>Recorded result SHA-256</dt><dd>{loaded.data.result_sha256}</dd><dt>Recorded request bundle SHA-256</dt><dd>{loaded.data.bundle_sha256}</dd></dl></details></section>
      {loaded.data.items.map(item=>{const value=feedback[item.slot]||blank();return <article className="panel evaluation-packet" key={item.slot}>
        <h2>{item.requested_state} · {label(item.signal_type)}</h2><p className="muted">Packet {item.slot} · Assessment date {item.as_of}</p>
        <div className="evaluation-columns"><section><h3>1. Retained source evidence</h3><p>Untrusted source content. An announcement is not confirmation that an event occurred.</p>
          {item.sources.map(source=>{const url=safeSourceUrl(source.url);return <details key={source.source_id}><summary>Evidence {source.source_id}</summary>{url?<a href={url} target="_blank" rel="noreferrer">Open original source</a>:<span>Source link unavailable</span>}<pre>{source.text}</pre></details>})}
        </section><section><h3>2. Model observation</h3><p className="muted">{item.model} · Inference, not analyst acceptance</p><p>{item.summary}</p>
          <details><summary>Original model dimensions</summary><dl>{Object.entries(item.model_dimensions).map(([k,v])=><div key={k}><dt>{label(k)}</dt><dd>{label(v)}</dd></div>)}</dl></details>
          <p>Cited evidence: {item.supported_source_ids.join(', ')||'None'}</p>
          {item.contradictions.length>0&&<><h4>Reported contradictions</h4><ul>{item.contradictions.map((q,i)=><li key={i}>{q}</li>)}</ul></>}
          <h4>Questions to resolve</h4><ul>{item.questions.map((q,i)=><li key={i}>{q}</li>)}</ul>
        </section></div>
        <section className="evaluation-context"><h3>3. Deterministic contextual assessment</h3><p>Based on {label(item.review_context.review_kind)} by {item.review_context.reviewer}. This is separate from your judgment.</p>
          <dl><div><dt>Operating evidence date</dt><dd>{item.review_context.operating_supported_on||'Unknown'} · {label(item.assessment.temporal_scope)}</dd></div><div><dt>Operations at assessment date</dt><dd>{label(item.assessment.operating_status_at_assessment)}</dd></div><div><dt>Requested-state operating relevance</dt><dd>{label(item.assessment.requested_state_operating_fit)}</dd></div><div><dt>Geographic basis</dt><dd>{label(item.review_context.geography_basis)} · {item.review_context.geography_state||'Unknown'}</dd></div><div><dt>Research guidance</dt><dd>{label(item.assessment.deterministic_research_disposition)}</dd></div></dl>
          <p>Operating evidence: {item.review_context.operating_source_ids.join(', ')||'None'} · Geographic evidence: {item.review_context.geography_source_ids.join(', ')||'None'}</p>
          <p>Unknown evidence stays useful for research. A non-qualifying role does not prove someone owns no shares. Geographic relevance does not establish current coverage.</p>
        </section>
        <fieldset><legend>4. Your usefulness judgment</legend><label>Usefulness for {item.slot}<select value={value.usefulness} onChange={e=>update(item.slot,{usefulness:e.target.value as Feedback['usefulness']})}><option value="">Not reviewed</option><option value="useful">Useful for triage</option><option value="not_useful">Not useful yet</option><option value="defer">Defer judgment</option></select></label>
          <label>Rationale for {item.slot}<textarea maxLength={4000} value={value.rationale} onChange={e=>update(item.slot,{rationale:e.target.value})} placeholder="What helped, what misled, or what is still missing?"/></label>
          <label>Review minutes for {item.slot} (optional)<input type="number" min="0" max="1440" step="any" value={value.review_minutes} onChange={e=>update(item.slot,{review_minutes:e.target.value})}/></label><small>Self-reported time spent reviewing, not time saved.</small>
        </fieldset>
      </article>})}
      <section className="panel evaluation-export"><h2>Keep your review</h2><label>Your name (self-reported)<input maxLength={200} value={reviewer} onChange={e=>setReviewer(e.target.value)}/></label><p>Export records only the judgments you selected. It does not accept model proposals, promote candidates or save feedback to the application.</p><button className="primary" onClick={download}>Download feedback JSON</button>{notice&&<p role="status">{notice}</p>}</section>
    </>}
  </div>;
}
