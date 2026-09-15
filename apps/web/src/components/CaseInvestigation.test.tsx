import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {CaseInvestigation} from './CaseInvestigation';

vi.mock('./AuthGate',()=>({useIdentity:()=>({role:'analyst'})}));
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
const source={id:7,url:'https://example.test/notice',publisher:'Fictional source',source_type:'other',access:'pending',reason:null,reviewer:null,reviewed_at:null,blocking_observations:[]};
function show(){render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}})}><CaseInvestigation caseId={24}/></QueryClientProvider>)}
const response=(value:unknown)=>new Response(JSON.stringify(value));
it('requires a rationale and reviewed conditions before approval, with no retrieval',async()=>{
  const posts:string[]=[];let saved=false;
  vi.stubGlobal('fetch',vi.fn(async(url:string,options?:RequestInit)=>{
    if(options?.method==='POST'){posts.push(url);saved=true;return response({...source,access:'approved'});}
    return response({items:url.includes('/sources')?[{...source,access:saved?'approved':'pending',reviewer:saved?'Human reviewer':null}]:[],has_next:false});
  }));show();
  await screen.findByRole('heading',{name:'Fictional source · source 7'});
  fireEvent.change(screen.getByLabelText('Access decision'),{target:{value:'approved'}});
  fireEvent.change(screen.getByLabelText('Access rationale'),{target:{value:'Public access reviewed'}});
  expect(screen.getByRole('button',{name:'Record access decision'})).toBeDisabled();
  fireEvent.click(screen.getByRole('checkbox'));
  fireEvent.click(screen.getByRole('button',{name:'Record access decision'}));
  await waitFor(()=>expect(posts).toEqual(['/api/research/cases/24/investigation/sources/7/access']));
  expect(await screen.findByText(/Reviewed by Human reviewer/)).toBeVisible();
  expect(screen.queryByRole('button',{name:'Record access decision'})).toBeNull();
});
it('renders retained text as text and keeps executive claims separate from ownership',async()=>{
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>response({items:url.includes('/claims')?[{id:3,subject:'person',predicate:'reported_role',value:{role:'executive'},relationship:'executive',classification:'source_fact',status:'asserted',authority:'secondary',directness:'reported'}]:url.includes('/evidence')?[{id:9,url:'javascript:alert(1)',publisher:'Retained source',classification:'source_fact',source_type:'other',published_at:null,retrieved_at:'2026-09-15T00:00:00Z',content_hash:'a'.repeat(64),artifact_id:4,excerpt:'<script>untrusted source</script>',excerpt_truncated:false}]:[],has_next:false})));
  show();await screen.findByRole('heading',{name:'Evidence 9 · Retained source'});
  expect(screen.getByText('Source URL unavailable')).toBeVisible();
  fireEvent.click(screen.getByText('Retained excerpt and provenance'));
  expect(screen.getByText('<script>untrusted source</script>')).toBeVisible();
  fireEvent.click(screen.getByRole('button',{name:'Inspect claims for evidence 9'}));
  expect(await screen.findByText(/Relationship: executive/)).toBeVisible();
});

it('loads source comparisons on request, explains uncertainty and paginates beyond visible evidence',async()=>{
  const calls:string[]=[];
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>{
    calls.push(url);
    if(url.includes('/comparisons'))return response({items:url.includes('page=2')?[]:[{evidence_id:30,publisher:'<b>Other source</b>',url:'javascript:alert(1)',relationship:'independent',rule:'no_shared_provenance_observed',explanation:'Independent reporting has not been verified.'}],has_next:!url.includes('page=2')});
    return response({items:url.includes('/evidence')?[{id:9,url:'https://example.test',publisher:'Retained source',classification:'source_fact',source_type:'other',published_at:null,retrieved_at:'2026-09-15T00:00:00Z',content_hash:'a'.repeat(64),artifact_id:4,excerpt:'Source text',excerpt_truncated:false}]:[],has_next:false});
  }));
  show();await screen.findByRole('heading',{name:'Evidence 9 · Retained source'});
  expect(calls.some(url=>url.includes('/comparisons'))).toBe(false);
  fireEvent.click(screen.getByRole('button',{name:'Compare source independence for evidence 9'}));
  expect(await screen.findByText('No shared provenance observed')).toBeVisible();
  expect(screen.getByText('Independent reporting has not been verified.')).toBeVisible();
  expect(screen.getByRole('heading',{name:'Compared with evidence 30 · <b>Other source</b>'})).toBeVisible();
  expect(screen.getByText('Source URL unavailable')).toBeVisible();
  fireEvent.click(screen.getByRole('button',{name:'Next comparisons for evidence 9'}));
  expect(await screen.findByText(/No comparisons on this page/)).toBeVisible();
  expect(calls).toContain('/api/research/cases/24/investigation/evidence/9/comparisons?page=2');
});

it('allows retry after a source-comparison read failure',async()=>{
  let failed=true;
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>{
    if(url.includes('/comparisons')){if(failed)throw new Error('Offline');return response({items:[],has_next:false});}
    return response({items:url.includes('/evidence')?[{id:9,url:'https://example.test',publisher:'Retained source',classification:'source_fact',source_type:'other',published_at:null,retrieved_at:'2026-09-15T00:00:00Z',content_hash:'a'.repeat(64),artifact_id:4,excerpt:'',excerpt_truncated:false}]:[],has_next:false});
  }));
  show();fireEvent.click(await screen.findByRole('button',{name:'Compare source independence for evidence 9'}));
  expect(await screen.findByText(/Comparisons unavailable/)).toBeVisible();
  failed=false;fireEvent.click(screen.getByRole('button',{name:'Try again'}));
  expect(await screen.findByText(/No other retained evidence to compare/)).toBeVisible();
});
