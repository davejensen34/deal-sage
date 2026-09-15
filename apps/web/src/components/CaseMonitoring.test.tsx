import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import {CaseMonitoring,MonitoringQueue} from './CaseMonitoring';
let role='analyst';
vi.mock('./AuthGate',()=>({useIdentity:()=>({role})}));
afterEach(()=>{cleanup();vi.unstubAllGlobals();role='analyst'});
function show(queue=false){render(<MemoryRouter><QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}>{queue?<MonitoringQueue/>:<CaseMonitoring caseId={25}/>}</QueryClientProvider></MemoryRouter>)}
it('retains the same personal schedule on a lost-response retry',async()=>{
  const posts:string[]=[];vi.stubGlobal('fetch',vi.fn(async(_url:string,options?:RequestInit)=>{
    if(options?.method==='POST'){posts.push(options.body as string);throw new Error('Response lost')}
    return new Response(JSON.stringify({latest:null,items:[],has_next:false,as_of:'2026-09-15'}));
  }));show();await waitFor(()=>expect(screen.getByRole('button',{name:'Set up or update monitoring'})).toBeEnabled());
  fireEvent.click(screen.getByRole('button',{name:'Set up or update monitoring'}));
  fireEvent.change(await screen.findByLabelText('Question to revisit'),{target:{value:'Has business identity evidence become available?'}});
  fireEvent.change(screen.getByLabelText('Reason for this schedule'),{target:{value:'Retain the unresolved case for later review.'}});
  fireEvent.click(screen.getByRole('button',{name:'Save monitoring'}));
  fireEvent.click(await screen.findByRole('button',{name:'Retry same monitoring update'}));
  await waitFor(()=>expect(posts).toHaveLength(2));expect(posts[0]).toBe(posts[1]);
  expect(JSON.parse(posts[0]).monitoring).toMatchObject({expected_prior_id:null,due_on:'2026-09-15',state:'active'});
});
it('keeps viewer monitoring read-only',async()=>{
  role='viewer';vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify({latest:null,items:[],has_next:false,as_of:'2026-09-15'}))));show();
  expect(await screen.findByText('This case is not in your monitoring queue.')).toBeVisible();
  expect(screen.queryByRole('button',{name:'Set up or update monitoring'})).toBeNull();
});
it('shows due work and changes queue scope without claiming a completed review',async()=>{
  const urls:string[]=[];vi.stubGlobal('fetch',vi.fn(async(url:string)=>{urls.push(url);return new Response(JSON.stringify({items:[],has_next:false,due_count:2,as_of:'2026-09-15'}))}));show(true);
  expect(await screen.findByText('2 cases due as of 2026-09-15 (UTC).')).toBeVisible();
  fireEvent.change(screen.getByLabelText('Show monitoring'),{target:{value:'paused'}});
  await waitFor(()=>expect(urls.some(u=>u.includes('scope=paused&page=1'))).toBe(true));
});
