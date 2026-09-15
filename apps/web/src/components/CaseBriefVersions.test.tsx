import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {CaseBriefVersions} from './CaseBriefVersions';
let role='analyst';
vi.mock('./AuthGate',()=>({useIdentity:()=>({role})}));
afterEach(()=>{cleanup();vi.unstubAllGlobals();role='analyst'});
const content={case_status:'open',source_brief:{title:'Fictional Acme',reported_names:[],category:'date_review',target_fit:'not_assessed',signal:null,timing:null,facts:[],conflicts:[],why_it_matters:'Research clue',next_gap:'Verify date',assessment_policy:null},sources:[],model_scope:{included:0,other_proposals:0},model_observations:[],reviews:[],conclusions:[],questions:[],transitions:[]};
const prepared={content,content_hash:'a'.repeat(64),latest_version:0,unchanged:false,changes:{sources:{added:[1],changed:[],removed:[]}}};
const saved={version:1,actor:'Human reviewer',created_at:'2026-09-15T00:00:00Z',content_hash:prepared.content_hash,content,changes:prepared.changes};
const response=(v:unknown)=>new Response(JSON.stringify(v));
function show(){render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}})}><CaseBriefVersions caseId={27}/></QueryClientProvider>)}

it('requires an explicit preview and reuses a lost-save identity to open the retained version',async()=>{
  const posts:string[]=[];let failed=true;
  vi.stubGlobal('fetch',vi.fn(async(url:string,options?:RequestInit)=>{
    if(options?.method==='POST'){posts.push(options.body as string);if(failed){failed=false;throw new Error('Response lost')}return response(saved);}
    if(url.endsWith('/brief-preview'))return response(prepared);
    if(url.endsWith('/brief-versions/1'))return response(saved);
    return response({items:posts.length?[saved]:[],has_next:false});
  }));show();
  expect(screen.queryByText('Preview current case brief')).toBeNull();
  fireEvent.click(screen.getByRole('button',{name:'Open brief versions'}));
  fireEvent.click(screen.getByRole('button',{name:'Preview current case brief'}));
  fireEvent.click(await screen.findByRole('button',{name:'Save this brief version'}));
  fireEvent.click(await screen.findByRole('button',{name:'Retry same brief save'}));
  await waitFor(()=>expect(posts.length).toBe(2));expect(posts[0]).toBe(posts[1]);
  expect(await screen.findByRole('heading',{name:'Saved version 1'})).toBeVisible();
  expect(screen.getByText(/Recorded by Human reviewer/)).toBeVisible();
});

it('keeps rejected model observations visibly distinct and disables viewer saves',async()=>{
  role='viewer';
  const data={...prepared,content:{...content,model_scope:{included:1,other_proposals:2},model_observations:[{id:8,evidence_id:4,provider:'fixture',model:'test',review_state:'reject',review_id:1,source_changed:true,observations:[{field:'business_name',value:'<script>Acme</script>',quote:'Quoted text',certainty:'tentative'}],unresolved_questions:[]}],reviews:[{id:1,proposal_id:8,analyst:'Human',decision:'reject',rationale:'Wrong context',corrected_output:null}]}};
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>response(url.endsWith('/brief-preview')?data:{items:[],has_next:false})));
  show();fireEvent.click(screen.getByRole('button',{name:'Open brief versions'}));fireEvent.click(screen.getByRole('button',{name:'Preview current case brief'}));
  expect(await screen.findByRole('button',{name:'Save this brief version'})).toBeDisabled();
  expect(screen.getByRole('heading',{name:'Proposal 8 · evidence 4 · reject'})).toBeVisible();
  expect(screen.getByText(/business name: <script>Acme/)).toBeVisible();
  expect(screen.getByText(/Source text or hash has changed/)).toBeVisible();
  expect(screen.getByText('Human: Wrong context')).toBeVisible();
});
