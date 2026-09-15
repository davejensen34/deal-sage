import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {BriefComparison} from './BriefComparison';
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
const version={version:1,actor:'Reviewer',created_at:'2026-09-15T00:00:00Z',content_hash:'abc'};
function show(){render(<QueryClientProvider client={new QueryClient()}><BriefComparison caseId={28}/></QueryClientProvider>)}
it('compares only on request and clears the result when selected versions change',async()=>{
  const fetcher=vi.fn(async(_url:string)=>new Response(JSON.stringify({from:version,to:{...version,version:2},unchanged:false,context_changes:[],groups:{sources:{counts:{added:0,changed:1,removed:0},rows:[{id:1,kind:'changed',fields:['relevant_excerpt'],before:{relevant_excerpt:'<script>untrusted()</script>'},after:{relevant_excerpt:'Unverified later report'}}]}}})));
  vi.stubGlobal('fetch',fetcher);show();expect(fetcher).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText('Later saved version'),{target:{value:'2'}});
  fireEvent.click(screen.getByRole('button',{name:'Compare these versions'}));
  expect(await screen.findByText('Saved version 1 → saved version 2')).toBeVisible();
  fireEvent.click(screen.getByText('Source reports and provenance: 0 added · 1 changed · 0 removed'));
  expect(screen.getByText(/<script>untrusted/)).toBeVisible();expect(document.querySelector('script')).toBeNull();
  expect(fetcher.mock.calls[0][0]).toContain('from_version=1&to_version=2');
  fireEvent.change(screen.getByLabelText('Later saved version'),{target:{value:'3'}});
  expect(screen.queryByText('Saved version 1 → saved version 2')).toBeNull();
});
it('explains invalid ordering and unchanged results',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify({from:version,to:version,unchanged:true,context_changes:[],groups:{}}))));show();
  fireEvent.change(screen.getByLabelText('Earlier saved version'),{target:{value:'2'}});
  expect(screen.getByRole('button',{name:'Compare these versions'})).toBeDisabled();
  fireEvent.change(screen.getByLabelText('Earlier saved version'),{target:{value:'1'}});
  fireEvent.click(screen.getByRole('button',{name:'Compare these versions'}));
  await waitFor(()=>expect(screen.getByText('No differences between these saved snapshots.')).toBeVisible());
});
