import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {DevelopmentHandoff} from './DevelopmentBrief';
import {apiDownload} from '../api/client';
vi.mock('../api/client',async importOriginal=>({...await importOriginal<typeof import('../api/client')>(),apiDownload:vi.fn().mockResolvedValue(undefined)}));
afterEach(()=>{cleanup();vi.unstubAllGlobals();vi.clearAllMocks()});
const packet={reviewer:'Named reviewer',reviewed_at:'2026-09-15T18:00:00Z',superseded_by_decision_id:8,boundaries:'Nothing has been sent.',reviewer_decision:{development:{summary:'A tentative opportunity for review.',unknowns:'Ownership and contact are unknown.',readiness:'not_ready',readiness_reason:'No source-backed contact.'}},contact_provenance:null,saved_brief:{version:1,content_hash:'frozen'}};
function show(canExport:boolean){vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify(packet))));render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><DevelopmentHandoff caseId={1} decisionId={4} canExport={canExport}/></QueryClientProvider>)}
it('marks superseded handoffs and exports the selected historical decision',async()=>{
  show(true);expect(await screen.findByText(/Historical handoff: superseded by decision 8/)).toBeVisible();
  fireEvent.click(screen.getByRole('button',{name:'Download reviewed handoff (.txt)'}));
  await waitFor(()=>expect(apiDownload).toHaveBeenCalledWith('/research/cases/1/decisions/4/development-brief/export',{},'dealsage-case-1-decision-4.txt'));
});
it('shows unknown contacts without enabling viewer export',async()=>{
  show(false);expect(await screen.findByText('Public business contact: unknown / not supplied.')).toBeVisible();
  expect(screen.queryByRole('button',{name:'Download reviewed handoff (.txt)'})).toBeNull();
});
