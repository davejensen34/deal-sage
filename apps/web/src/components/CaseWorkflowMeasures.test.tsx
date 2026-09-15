import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import {CaseWorkflowMeasures} from './CaseWorkflowMeasures';
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
function show(){render(<MemoryRouter><QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><CaseWorkflowMeasures/></QueryClientProvider></MemoryRouter>)}
const data={total_cases:0,cases_with_decisions:0,cases_without_decisions:0,decisions:{},purposes:[{purpose:'marketing_introduction',decisions:0,useful:0,not_useful:0,missing_judgments:0,assessed:0,useful_percent:null,timed_reviews:0,median_review_seconds:null}],reservations:[],items:[],has_next:false,measurement_scope:'Latest shared decision per case.',cost_scope:'Reservations are not actual spend.'};
it('shows missing measurements without turning them into successful reviews',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify(data))));show();
  expect(await screen.findByText(/No research cases yet/)).toBeVisible();
  expect(screen.getByText(/0 useful \/ 0 assessed.*Not measured/)).toBeVisible();
  expect(screen.getByText(/Median self-reported.*Not measured/)).toBeVisible();
});
it('retains negative reasons as inert text and offers paginated case links',async()=>{
  const fetcher=vi.fn(async(url:string)=>new Response(JSON.stringify({...data,total_cases:11,cases_with_decisions:11,has_next:!url.endsWith('page=2'),items:[{id:1,case_id:28,actor:'QA',created_at:'2026-09-15T00:00:00Z',decision:{brief_version:2,purpose:'marketing_introduction',outcome:'dismiss',feedback:{usefulness:'not_useful',reason:'<script>untrusted()</script>',review_seconds:120}}}]})));
  vi.stubGlobal('fetch',fetcher);show();
  expect(await screen.findByRole('link',{name:'Case 28 · dismiss'})).toHaveAttribute('href','/research/cases/28');
  expect(screen.getByText(/<script>untrusted/)).toBeVisible();expect(document.querySelector('script')).toBeNull();
  fireEvent.click(screen.getByRole('button',{name:'Next reviews'}));
  expect(await screen.findByRole('button',{name:'Next reviews'})).toBeDisabled();
  expect(fetcher.mock.calls.some(c=>c[0].endsWith('page=2'))).toBe(true);
});
it('explains load failures and supports retry',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>{throw new Error('Unavailable')}));show();
  expect(await screen.findByRole('alert')).toHaveTextContent('Case review measures unavailable');
  expect(screen.getByRole('button',{name:'Retry measures'})).toBeVisible();
});
