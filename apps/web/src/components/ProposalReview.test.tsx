import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import {ProposalReview} from './ProposalReview';

const proposal={id:4,task:'business_extraction',provider:'fixture',model:'fixture-v1',prompt_version:'business-v1',schema_version:'business-v1',execution_outcome:'completed',proposed_output:{summary:'Possible business'},supported_evidence_ids:[12],supported_claim_ids:[18],input_tokens:40,output_tokens:10,latency_ms:25,cost_cents:0,error_class:null,created_at:'2026-09-08T00:00:00Z',dispositions:[]};

describe('ProposalReview',()=>{
  afterEach(()=>vi.restoreAllMocks());
  it('keeps model output distinct and records an analyst disposition',async()=>{
    const fetchMock=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({id:1,decision:'accept'}),{status:200,headers:{'Content-Type':'application/json'}}));
    render(<QueryClientProvider client={new QueryClient()}><ProposalReview proposal={proposal}/></QueryClientProvider>);
    expect(screen.getByText('Possible business')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Decision'),{target:{value:'accept'}});
    fireEvent.change(screen.getByLabelText('Rationale'),{target:{value:'Supported by the cited evidence.'}});
    fireEvent.click(screen.getByRole('button',{name:/record accept/i}));
    await waitFor(()=>expect(fetchMock).toHaveBeenCalledOnce());
    const request=fetchMock.mock.calls[0][1] as RequestInit;
    expect(JSON.parse(request.body as string)).toEqual({decision:'accept',rationale:'Supported by the cited evidence.'});
  });
});
