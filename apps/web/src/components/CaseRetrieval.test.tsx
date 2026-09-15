import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {RetrieveSource,RetrievalHistory} from './CaseRetrieval';
vi.mock('./AuthGate',()=>({useIdentity:()=>({role:'operator'})}));
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
const history={provider:'fixture',policy:{max_bytes:1000000,timeout_seconds:20,max_source_attempts:3,max_case_attempts:20},attempts:[]};
function show(){render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}})}><RetrieveSource caseId={24} sourceId={1} url="https://example.test/fictional-discovery/0"/><RetrievalHistory caseId={24}/></QueryClientProvider>)}
it('keeps the same request key after a lost response and shows retained evidence',async()=>{
  let complete=false;const bodies:string[]=[];
  vi.stubGlobal('fetch',vi.fn(async(url:string,options?:RequestInit)=>{
    if(options?.method==='POST'){bodies.push(String(options.body));if(bodies.length===1)throw Error('Connection lost');complete=true;return new Response('{}');}
    return new Response(JSON.stringify({...history,attempts:complete?[{id:1,source_id:1,status:'succeeded',actor:'Operator',evidence_id:9,error_code:null}]:[]}));
  }));show();
  await waitFor(()=>expect(screen.getByRole('button',{name:'Retrieve one document'})).toBeEnabled());
  expect(bodies).toHaveLength(0);fireEvent.click(screen.getByRole('button',{name:'Retrieve one document'}));
  await screen.findByRole('alert');fireEvent.click(screen.getByRole('button',{name:'Retry same retrieval request'}));
  expect(await screen.findByText(/retained evidence #9/)).toBeVisible();expect(bodies[0]).toBe(bodies[1]);
});
it('disables new retrieval while an interrupted attempt is awaiting recovery',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify({...history,attempts:[{id:7,source_id:1,status:'running',actor:'Operator',recovery_after:'2099-01-01T00:00:00Z'}]}))));show();
  await screen.findByText(/Attempt 7/);expect(screen.getByRole('button',{name:'Retrieve one document'})).toBeDisabled();
  expect(screen.getByRole('button',{name:'Recover interrupted retrieval 7'})).toBeDisabled();
});
