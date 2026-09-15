import {afterEach, expect, it, vi} from 'vitest';
import {cleanup, fireEvent, render, screen} from '@testing-library/react';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter, Route, Routes} from 'react-router-dom';
import {CandidateDetail} from './CandidateDetail';

vi.mock('../components/AuthGate',()=>({useIdentity:()=>({role:'viewer'})}));
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
function show() {
  render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><MemoryRouter initialEntries={['/candidates/1']}><Routes><Route path="/candidates/:id" element={<CandidateDetail/>}/></Routes></MemoryRouter></QueryClientProvider>);
}
it('renders source origin and score provenance without requiring an existing review',async()=>{
  const source={is_demo:false,publisher:'Test source',canonical_url:'https://example.test'};
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify({
    business:{legal_name:'Example business',city:'Ogden',state:'UT'},person:{full_name:'Example person'},
    signal:{signal_type:'retirement',source},status:'needs_review',last_researched_at:null,
    relationship:{relationship_type:'executive',active:null},scores:{business_relationship:20,signal_identity:30,overall_candidate:20},
    score_provenance:{method_version:'candidate-score-v1',classification:'evidence_derived',supporting_evidence_ids:[1],factors:[{feature:'role_scope',impact:0}],calculation:{overall:20},calculated_at:'2026-09-15'},
    positive_signals:[],conflicting_signals:[],missing_evidence:[],review:null,audit:[],
    evidence:[{id:1,evidence_type:'business',classification:'third_party_estimate',source,evidence_strength:'low',retrieved_at:null}],
  }))));show();
  expect(await screen.findByRole('heading',{name:'Example business'})).toBeVisible();
  expect(screen.queryByText(/Fictional demo/)).toBeNull();
  expect(screen.getByText('third party estimate')).toBeVisible();
  fireEvent.click(screen.getByText('Score provenance and calculation'));
  expect(screen.getByText(/candidate-score-v1 · evidence derived/)).toBeVisible();
  expect(screen.getByText('No notes yet.')).toBeVisible();
  expect(screen.queryByRole('button',{name:'Validate'})).toBeNull();
  expect(screen.getByRole('button',{name:'Generate summary'})).toBeDisabled();
  expect(screen.getByRole('button',{name:'Add note'})).toBeDisabled();
});
it('shows a recoverable missing-candidate state',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify({detail:'Candidate not found'}),{status:404})));show();
  expect(await screen.findByRole('alert')).toHaveTextContent('Candidate unavailable');
  expect(screen.getByRole('link',{name:'Back to candidates'})).toHaveAttribute('href','/candidates');
});
