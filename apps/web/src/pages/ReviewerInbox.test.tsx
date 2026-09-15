import {afterEach, expect, it, vi} from 'vitest';
import {cleanup, fireEvent, render, screen} from '@testing-library/react';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter, Route, Routes} from 'react-router-dom';
import {ReviewerInbox, ResearchCaseDetail} from './ReviewerInbox';

afterEach(()=>{cleanup();vi.unstubAllGlobals()});
function show(path='/') {
  render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><MemoryRouter initialEntries={[path]}><Routes><Route path="/" element={<ReviewerInbox/>}/><Route path="/research/cases/:id" element={<ResearchCaseDetail/>}/></Routes></MemoryRouter></QueryClientProvider>);
}
it('keeps unknown businesses, analyst attribution and URL-based pagination', async()=>{
  const fetcher=vi.fn(async(_url:string)=>new Response(JSON.stringify({cases:[{id:23,origin_strategy:'signal_first',status:'open',stop_reason:null,linked_business:null,candidate_match_id:null,transitions:[],conclusion:null,lead_brief:{title:'Business not yet identified',next_gap:'Find an explicit company clue.'}}],total:23,page:1,page_size:10})));
  vi.stubGlobal('fetch',fetcher);show();
  expect(await screen.findByRole('heading',{name:'Business not yet identified'})).toBeVisible();
  expect(screen.getByText('No reviewer conclusion recorded')).toBeVisible();
  expect(screen.getByRole('link',{name:'Open research brief →'})).toHaveAttribute('href','/research/cases/23');
  fireEvent.click(screen.getByRole('button',{name:'Next'}));
  await screen.findByText('Page 2 of 3');
  expect(fetcher.mock.calls.some(([url])=>String(url).includes('page=2'))).toBe(true);
  fireEvent.change(screen.getByLabelText('State'),{target:{value:'UT'}});
  await screen.findByText('Page 1 of 3');
  expect(fetcher.mock.calls.some(([url])=>String(url).includes('state=UT'))).toBe(true);
});
it('explains a fresh workspace without inventing research or an execution button',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify({cases:[],total:0,page:1,page_size:10}))));show();
  expect(await screen.findByRole('heading',{name:'No research cases match'})).toBeVisible();
  expect(screen.getByRole('link',{name:'Review existing candidates'})).toHaveAttribute('href','/candidates');
});
it('handles a missing case without dereferencing nonexistent evidence',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify({detail:'Research case not found'}),{status:404})));show('/research/cases/999');
  expect(await screen.findByRole('alert')).toHaveTextContent('Research case not found');
  expect(screen.getByRole('button',{name:'Try again'})).toBeEnabled();
});
