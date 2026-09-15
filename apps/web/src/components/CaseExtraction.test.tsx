import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {ExtractEvidence,ExtractionHistory} from './CaseExtraction';
let role='operator';
vi.mock('./AuthGate',()=>({useIdentity:()=>({role})}));
afterEach(()=>{cleanup();vi.unstubAllGlobals();role='operator'});
const policy={provider:'fixture',model:'fictional-extractor-v1',ready:true,reason:'Fictional offline extraction',reserved_cents:0,max_output_tokens:1000,timeout_seconds:30,max_attempts:2,max_cost_cents:25};
const packet={evidence_id:6,excerpt:'Fictional Acme makes widgets.',publisher:'Fixture',content_hash:'a'.repeat(64),published_at:null};
const preview={plan_hash:'b'.repeat(64),plan:{policy,packet}};
const response=(data:unknown)=>new Response(JSON.stringify(data));
function show(){render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}})}><ExtractEvidence caseId={25} evidenceId={6}/><ExtractionHistory caseId={25}/></QueryClientProvider>)}

it('previews explicitly and reuses the request identity after a lost response',async()=>{
  const payloads:string[]=[];let failed=true;
  vi.stubGlobal('fetch',vi.fn(async(url:string,options?:RequestInit)=>{
    if(url.endsWith('/extraction-preview'))return response(preview);
    if(options?.method==='POST'){payloads.push(options.body as string);if(failed){failed=false;throw new Error('Lost response')}return response({status:'completed'});}
    return response({policy,attempts:[]});
  }));show();
  expect(screen.queryByText('Fictional offline extraction')).toBeNull();
  fireEvent.click(screen.getByRole('button',{name:'Prepare extraction for evidence 6'}));
  fireEvent.click(screen.getByRole('button',{name:'Preview extraction packet'}));
  expect(await screen.findByText('Fictional offline extraction')).toBeVisible();
  fireEvent.click(screen.getByRole('button',{name:'Authorize one extraction'}));
  fireEvent.click(await screen.findByRole('button',{name:'Retry same extraction request'}));
  await waitFor(()=>expect(payloads.length).toBe(2));expect(payloads[0]).toBe(payloads[1]);
  expect(JSON.parse(payloads[0]).expected_hash).toBe(preview.plan_hash);
});

it('keeps viewer execution disabled and renders model quotes as text',async()=>{
  role='viewer';
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>response(url.endsWith('/extraction-preview')?preview:{policy,attempts:[{id:1,evidence_id:6,actor:'Operator',status:'completed',error_code:null,reserved_cents:0,recovery_after:'2026-09-15T00:00:00Z',policy,packet,proposal:{id:8,outcome:'completed',input_tokens:null,output_tokens:null,cost_cents:0,output:{observations:[{field:'business_name',value:'<b>Acme</b>',quote:'<script>source text</script>',certainty:'tentative'}],unresolved_questions:['Ownership is unknown.']}}}] })));show();
  expect(await screen.findByText('<script>source text</script>')).toBeVisible();
  expect(screen.getByText(/estimated cost: unknown/)).toBeVisible();
  expect(screen.getByText(/field meaning remains unverified/)).toBeVisible();
  fireEvent.click(screen.getByRole('button',{name:'Prepare extraction for evidence 6'}));
  fireEvent.click(screen.getByRole('button',{name:'Preview extraction packet'}));
  expect(await screen.findByRole('button',{name:'Authorize one extraction'})).toBeDisabled();
});
