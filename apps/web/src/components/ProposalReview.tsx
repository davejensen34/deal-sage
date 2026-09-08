import {useState} from 'react';
import {useMutation,useQueryClient} from '@tanstack/react-query';
import {Bot,CheckCircle2,Clock3,PencilLine,XCircle} from 'lucide-react';
import {api} from '../api/client';

export type ProposalDisposition={id:number;decision:string;rationale:string;corrected_output:Record<string,unknown>|null;analyst:string;created_at:string};
export type ModelProposal={id:number;task:string;provider:string;model:string;prompt_version:string;schema_version:string;execution_outcome:string;proposed_output:Record<string,unknown>|null;supported_evidence_ids:number[];supported_claim_ids:number[];input_tokens:number|null;output_tokens:number|null;latency_ms:number|null;cost_cents:number;error_class:string|null;created_at:string;dispositions:ProposalDisposition[]};

const label=(value:string)=>value.replaceAll('_',' ');

export function ProposalReview({proposal}:{proposal:ModelProposal}){
  const queryClient=useQueryClient();
  const [decision,setDecision]=useState<'accept'|'correct'|'reject'|'defer'>('defer');
  const [rationale,setRationale]=useState('');
  const [correction,setCorrection]=useState('');
  const [error,setError]=useState('');
  const mutation=useMutation({
    mutationFn:async()=>{
      let corrected_output:Record<string,unknown>|undefined;
      if(decision==='correct'){
        try{corrected_output=JSON.parse(correction)}catch{throw new Error('Correction must be valid JSON.')}
      }
      return api(`/research/model-proposals/${proposal.id}/dispositions`,{method:'POST',body:JSON.stringify({decision,rationale,corrected_output})});
    },
    onSuccess:()=>{setRationale('');setCorrection('');setError('');queryClient.invalidateQueries({queryKey:['research-case-narratives']})},
    onError:(reason)=>setError(reason instanceof Error?reason.message:'Disposition failed'),
  });
  const completed=proposal.execution_outcome==='completed';
  return <article className="proposal-review">
    <div className="proposal-heading"><Bot/><div><b>Model proposal · {label(proposal.task)}</b><small>{proposal.provider} · {proposal.model} · {proposal.prompt_version}</small></div><span>{label(proposal.execution_outcome)}</span></div>
    {proposal.proposed_output?<dl className="proposal-output">{Object.entries(proposal.proposed_output).map(([key,value])=><div key={key}><dt>{label(key)}</dt><dd>{typeof value==='string'?value:JSON.stringify(value)}</dd></div>)}</dl>:<p className="muted">No provider output was retained. {proposal.error_class&&`Safe failure class: ${proposal.error_class}.`}</p>}
    <p className="proposal-provenance">Evidence {proposal.supported_evidence_ids.join(', ')||'none'} · Claims {proposal.supported_claim_ids.join(', ')||'none'} · {proposal.input_tokens??'–'} in / {proposal.output_tokens??'–'} out · {proposal.latency_ms??'–'} ms</p>
    {proposal.dispositions.map(item=><div className={`proposal-disposition ${item.decision}`} key={item.id}><CheckCircle2/><div><b>Analyst · {label(item.decision)}</b><p>{item.rationale}</p><small>{item.analyst}</small>{item.corrected_output&&<p><b>Correction:</b> {JSON.stringify(item.corrected_output)}</p>}</div></div>)}
    <div className="proposal-actions" aria-label="Proposal disposition">
      <label>Decision<select value={decision} onChange={event=>setDecision(event.target.value as typeof decision)}><option value="accept" disabled={!completed}>Accept</option><option value="correct" disabled={!completed}>Correct</option><option value="reject">Reject</option><option value="defer">Defer</option></select></label>
      <label>Rationale<textarea value={rationale} onChange={event=>setRationale(event.target.value)} placeholder="Explain the evidence-backed decision"/></label>
      {decision==='correct'&&<label>Corrected structured output<textarea value={correction} onChange={event=>setCorrection(event.target.value)} placeholder='{"summary":"Corrected observation"}'/></label>}
      {error&&<p className="form-error">{error}</p>}
      <button onClick={()=>mutation.mutate()} disabled={mutation.isPending||rationale.trim().length<3}>{decision==='accept'?<CheckCircle2/>:decision==='correct'?<PencilLine/>:decision==='reject'?<XCircle/>:<Clock3/>}Record {decision}</button>
    </div>
  </article>;
}
