export type TransitionReviewItem={
  claim_id:number;evidence_id:number;signal_type:string;subject_type:string;
  person:string|null;business:string|null;event_date:string|null;event_status:string;
  publication_date:string|null;retrieved_at:string;publisher:string;canonical_url:string;
  classification:string;claim_status:string;policy_version:string|null;
  policy:{label:string;evidence_requirements:string[];temporal_questions:string[];ownership_limitations:string[];review_questions:string[]}|null;
  uncertainties:string[];
};

const label=(value:string)=>value.replaceAll('_',' ');
const dateLabel=(value:string|null)=>value?value.slice(0,10):'Unknown';

export function TransitionReview({items}:{items:TransitionReviewItem[]}){
  if(!items.length)return null;
  return <section aria-label="Transition evidence review">
    <h3>Transition evidence review</h3>
    <p>Source-reported claims guide investigation. They do not establish ownership, event completion, or an analyst decision.</p>
    {items.map(item=><article key={item.claim_id} className="panel">
      <h4>{item.policy?.label||label(item.signal_type)} · {item.business||item.person||'Subject unresolved'}</h4>
      <p><b>Source claim #{item.claim_id}</b> · {label(item.classification)} · {label(item.claim_status)}</p>
      <p>Subject scope: {label(item.subject_type)}{item.person&&<> · Person: {item.person}</>}{item.business&&<> · Business: {item.business}</>}</p>
      <p>Event date: <b>{dateLabel(item.event_date)}</b> · Event status: <b>{label(item.event_status)}</b><br/>
        Published: {dateLabel(item.publication_date)} · Retrieved: {dateLabel(item.retrieved_at)}</p>
      <p>{/^https?:\/\//i.test(item.canonical_url)?<a href={item.canonical_url} target="_blank" rel="noreferrer">{item.publisher} · Evidence #{item.evidence_id}</a>:<span>{item.publisher} · Evidence #{item.evidence_id}</span>}</p>
      <ul>{item.uncertainties.map(question=><li key={question}>{question}</li>)}</ul>
      {item.policy?<>
        <h4>Research guidance · {item.policy_version}</h4>
        <ul>{item.policy.ownership_limitations.map(note=><li key={note}>{note}</li>)}</ul>
        <h4>Questions to resolve</h4>
        <ul>{[...item.policy.evidence_requirements,...item.policy.temporal_questions,...item.policy.review_questions].map(question=><li key={question}>{question}</li>)}</ul>
      </>:<p>No reviewed policy is available. Keep this clue in research until its type is resolved.</p>}
    </article>)}
  </section>;
}
