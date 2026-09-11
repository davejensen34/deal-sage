import {render,screen,fireEvent,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {describe,expect,it,vi} from 'vitest';
import {DiscoveryLead,DiscoveryLeads} from './DiscoveryLeads';
import {api} from '../api/client';
vi.mock('../api/client',()=>({api:vi.fn()}));
const lead:DiscoveryLead={id:3,url:'https://example.test/lead',publisher:'Example directory',source_type:'business_directory',relevance:'Possible business clue',proposed_use:'case_specific_research',provider:'fixture',query_ids:[1,2],evidence_ids:[],access:'blocked',access_reason:'Access unavailable',priority:20,method:'discovery-priority-v1',factors:[{reason:'A retained discovery clue can guide investigation',points:20}],next_action:'find_alternative',question:'Find an accessible independent source',frontier_id:null,frontier_status:null};
function show(open:boolean){render(<QueryClientProvider client={new QueryClient()}><DiscoveryLeads caseId={1} open={open} leads={[lead]}/></QueryClientProvider>)}
describe('discovery clues',()=>{
  it('keeps unverified clues visible and priority distinct from opportunity confidence',()=>{
    show(false);
    expect(screen.getByText('Research priority 20/100')).toBeInTheDocument();
    expect(screen.getByText(/not a probability/)).toBeInTheDocument();
    expect(screen.getByText(/not a disproven claim/)).toBeInTheDocument();
    expect(screen.getByRole('button',{name:'Queue follow-up question'})).toBeDisabled();
  });
  it('queues only a question and reports server refusal',async()=>{
    vi.mocked(api).mockRejectedValueOnce(new Error('Review permission required'));
    show(true);
    fireEvent.click(screen.getByRole('button',{name:'Queue follow-up question'}));
    await waitFor(()=>expect(screen.getByRole('alert')).toHaveTextContent('Review permission required'));
    expect(api).toHaveBeenCalledWith('/research/cases/1/discovery-leads/3/follow-up',{method:'POST'});
  });
});
