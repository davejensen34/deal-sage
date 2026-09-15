import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {CaseDecisions} from './CaseDecisions';
let role='analyst';
vi.mock('./AuthGate',()=>({useIdentity:()=>({role})}));
afterEach(()=>{cleanup();vi.unstubAllGlobals();role='analyst'});
const brief={version:1,actor:'Reviewer',content:{source_brief:{title:'Fictional business'},sources:[{id:7,publisher:'Fictional Source',relevant_excerpt:'Uncertain business clue'}]}};
function show(){render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><CaseDecisions caseId={1}/></QueryClientProvider>)}
it('ties a decision to reviewed sources and retries a lost response with the same payload',async()=>{
  const posts:string[]=[];vi.stubGlobal('fetch',vi.fn(async(url:string,options?:RequestInit)=>{
    if(options?.method==='POST'){posts.push(options.body as string);throw new Error('Response lost')}
    return new Response(JSON.stringify(url.endsWith('/brief-versions/1')?brief:{items:[],has_next:false,latest:null}));
  }));show();await waitFor(()=>expect(screen.getByRole('button',{name:'Load reviewed brief'})).toBeEnabled());
  fireEvent.click(screen.getByRole('button',{name:'Load reviewed brief'}));
  fireEvent.change(await screen.findByLabelText('Decision rationale'),{target:{value:'There is not enough evidence of ownership.'}});
  fireEvent.change(screen.getByLabelText('Next action'),{target:{value:'Check independent official records.'}});
  fireEvent.click(screen.getByLabelText('Supports decision · evidence 7'));
  fireEvent.change(screen.getByLabelText('Usefulness for this purpose'),{target:{value:'not_useful'}});
  fireEvent.change(screen.getByLabelText('Usefulness reason'),{target:{value:'Missing identity evidence for this purpose.'}});
  fireEvent.change(screen.getByLabelText('Self-reported review seconds'),{target:{value:'120'}});
  fireEvent.click(screen.getByRole('button',{name:'Record reviewer decision'}));
  fireEvent.click(await screen.findByRole('button',{name:'Retry same decision'}));
  await waitFor(()=>expect(posts.length).toBe(2));expect(posts[0]).toBe(posts[1]);expect(JSON.parse(posts[0]).decision.supporting_source_ids).toEqual([7]);expect(JSON.parse(posts[0]).decision.feedback).toEqual({usefulness:'not_useful',reason:'Missing identity evidence for this purpose.',review_seconds:120});
});
it('keeps viewers read-only',async()=>{
  role='viewer';vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify({items:[],has_next:false,latest:null}))));show();
  expect(await screen.findByText('No workflow decision recorded.')).toBeVisible();expect(screen.queryByRole('button',{name:'Load reviewed brief'})).toBeNull();
});

it('records a development handoff with explicit unknowns and no invented contact',async()=>{
  const posts:string[]=[];
  vi.stubGlobal('fetch',vi.fn(async(url:string,options?:RequestInit)=>{
    if(options?.method==='POST'){posts.push(options.body as string);throw new Error('Response lost')}
    return new Response(JSON.stringify(url.endsWith('/brief-versions/1')?brief:{items:[],has_next:false,latest:null}));
  }));show();await waitFor(()=>expect(screen.getByRole('button',{name:'Load reviewed brief'})).toBeEnabled());
  fireEvent.click(screen.getByRole('button',{name:'Load reviewed brief'}));
  fireEvent.change(await screen.findByLabelText('Decision'),{target:{value:'create_development_brief'}});
  for(const [label,value] of Object.entries({'Decision rationale':'This may fit a continuity advisory purpose.','Next action':'Research the business contact before communication.','Opportunity summary':'A fictional continuity introduction for later review.','Unknowns and limitations':'Ownership and sale intent remain unknown.','Readiness rationale':'No public business contact has been retained.'}))
    fireEvent.change(screen.getByLabelText(label),{target:{value}});
  fireEvent.click(screen.getByRole('button',{name:'Record reviewer decision'}));
  fireEvent.click(await screen.findByRole('button',{name:'Retry same decision'}));
  await waitFor(()=>expect(posts).toHaveLength(2));expect(posts[0]).toBe(posts[1]);
  const d=JSON.parse(posts[0]).decision;expect(d.outcome).toBe('create_development_brief');expect(d.development.readiness).toBe('not_ready');expect(d.development.contact).toBeUndefined();
});
