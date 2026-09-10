import {render,screen} from '@testing-library/react';
import {describe,expect,it} from 'vitest';
import {RefreshHistory,SourceRefresh} from './SourceRefreshes';

describe('RefreshHistory',()=>{
  it('shows bounded outcome, freshness, and cost',()=>{
    const row:SourceRefresh={id:1,source_key:'colorado_business_entities',jurisdiction:'Colorado',requested_by:'Morgan Lee',status:'succeeded',record_limit:25,approved_cost_usd:0,actual_cost_usd:0,freshness_status:'not_measurable_from_record',freshness_reason:'Dataset metadata must be checked.',started_at:'2026-09-10T18:00:00Z',finished_at:'2026-09-10T18:00:01Z',result_summary:{retrieved:25,curated:50}};
    render(<RefreshHistory rows={[row]}/>);
    expect(screen.getByText('Colorado · succeeded')).toBeInTheDocument();
    expect(screen.getByText(/25 record limit/)).toBeInTheDocument();
    expect(screen.getByText(/not measurable from record/)).toBeInTheDocument();
    expect(screen.getByText('$0.00')).toBeInTheDocument();
  });
});
