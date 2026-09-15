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
