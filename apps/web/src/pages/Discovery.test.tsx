import {afterEach, expect, it, vi} from 'vitest';
import {cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter, Route, Routes} from 'react-router-dom';
import {Discovery, DiscoveryRun} from './Discovery';

vi.mock('../components/AuthGate',()=>({useIdentity:()=>({role:'demo'})}));
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
const config={origin:'signal_first',objective:'Find recent transitions worth reviewing',business_name:'',states:['CO'],signals:['retirement'],lookback_days:90,max_records:25,max_queries:3,max_cost_cents:100,max_elapsed_seconds:900};
const plan={version:'discovery-run-v1',settings:config,policy:{assessment_date:'2026-09-15'},queries:['Fictional query'],submitted_queries:['Fictional query after:2026-06-16'],provider:{key:'fixture',model:null,ready:true,reason:'Fictional demo; no network calls',reservation_cents:0,max_results:5,timeout_seconds:5}};
function show(path='/discover') {
  render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}})}><MemoryRouter initialEntries={[path]}><Routes><Route path="/discover" element={<Discovery/>}/><Route path="/discover/runs/:id" element={<DiscoveryRun/>}/></Routes></MemoryRouter></QueryClientProvider>);
}
const response=(value:unknown)=>new Response(JSON.stringify(value));
it('previews name-free discovery and invalidates preview after limits change',async()=>{
  const fetcher=vi.fn(async(url:string)=>url.endsWith('/defaults')?response({profile_id:null,settings:config}):url.endsWith('/preview')?response({plan,hash:'a'.repeat(64)}):response({items:[],has_next:false}));
  vi.stubGlobal('fetch',fetcher);show();
  await screen.findByRole('button',{name:'Preview plan'});
  expect(screen.getByLabelText('Business name (optional)')).not.toBeRequired();
  fireEvent.click(screen.getByRole('button',{name:'Preview plan'}));
  expect(await screen.findByRole('heading',{name:'Bounded discovery plan'})).toBeVisible();
  expect(screen.getByRole('button',{name:'Save research plan'})).toBeEnabled();
  expect(fetcher.mock.calls.some(([url])=>url.endsWith('/execute'))).toBe(false);
  fireEvent.change(screen.getByLabelText('Maximum source links'),{target:{value:'50'}});
  expect(screen.queryByRole('button',{name:'Save research plan'})).toBeNull();
  fireEvent.change(screen.getByLabelText('Starting point'),{target:{value:'business_first'}});
  expect(screen.getByLabelText('Business name (required)')).toBeRequired();
});
it('retries a lost transport response with the same attempt key and revision',async()=>{
  const run={id:1,case_id:24,plan,status:'ready',revision:0,next_slot:0,reserved_cents:0,record_count:0,deadline_at:null,attempts:[]};
  const bodies:string[]=[];
  vi.stubGlobal('fetch',vi.fn(async(url:string,options?:RequestInit)=>{
    if(url.endsWith('/execute')){bodies.push(String(options?.body));if(bodies.length===1)throw new Error('Connection lost');return response({...run,status:'completed',revision:2,next_slot:1});}
    return response(run);
  }));show('/discover/runs/1');
  fireEvent.click(await screen.findByRole('button',{name:'Run next search'}));
  await screen.findByRole('alert');
  fireEvent.click(screen.getByRole('button',{name:'Retry same request'}));
  await waitFor(()=>expect(bodies).toHaveLength(2));
  expect(bodies[0]).toBe(bodies[1]);
  expect(JSON.parse(bodies[0]).expected_revision).toBe(0);
});

it('explains the reported two-state six-family scope and adjusts attempts only on request',async()=>{
  const selected={...config,origin:'hybrid',states:['CO','TX'],signals:['possible_death','retirement','succession','ownership_change','founder_exit','restructuring'],lookback_days:30,max_records:50};
  const fetcher=vi.fn(async(url:string)=>url.endsWith('/defaults')?response({profile_id:null,settings:selected}):url.endsWith('/preview')?response({plan:{...plan,settings:{...selected,max_queries:12}},hash:'b'.repeat(64)}):response({items:[],has_next:false}));
  vi.stubGlobal('fetch',fetcher);show();
  expect(await screen.findByText('2 states × 6 transition families = 12 planned queries.')).toBeVisible();
  expect(screen.getByRole('button',{name:'Preview plan'})).toBeDisabled();
  expect(screen.getByRole('button',{name:'Save as workspace defaults'})).toBeDisabled();
  expect(screen.getByLabelText('Total query attempts (including retries)')).toHaveValue(3);
  fireEvent.click(screen.getByRole('button',{name:'Set attempt limit to 12'}));
  expect(screen.getByLabelText('Total query attempts (including retries)')).toHaveValue(12);
  expect(screen.getByLabelText('Reservation ceiling (USD cents)')).toHaveValue(100);
  expect(screen.getByLabelText('Maximum source links')).toHaveValue(50);
  expect(screen.getByRole('button',{name:'Preview plan'})).toBeEnabled();
  expect(fetcher.mock.calls.some(([url])=>url.endsWith('/preview'))).toBe(false);
  fireEvent.click(screen.getByRole('button',{name:'Preview plan'}));
  await screen.findByRole('heading',{name:'Bounded discovery plan'});
  fireEvent.click(screen.getByLabelText('CO'));
  fireEvent.click(screen.getByLabelText('TX'));
  expect(screen.getByText('Select at least one state and one transition family to prepare a plan.')).toBeVisible();
  expect(screen.getByRole('button',{name:'Preview plan'})).toBeDisabled();
  expect(screen.queryByRole('button',{name:'Save research plan'})).toBeNull();
});
