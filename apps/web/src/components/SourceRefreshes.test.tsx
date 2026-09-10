import {render,screen} from '@testing-library/react';
import {describe,expect,it} from 'vitest';
import {AlertInbox,RefreshHistory,SourceRefresh} from './SourceRefreshes';

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

it('renders unread in-app alerts with their safe failure detail',()=>{
  render(<AlertInbox alerts={[{id:2,source_refresh_id:9,event_type:'refresh_failed',title:'Colorado refresh failed',detail:'Safe failure code: ConnectError.',created_at:'2026-09-10T18:00:00Z'}]}/>);
  expect(screen.getByText('Colorado refresh failed')).toBeInTheDocument();
  expect(screen.getByText(/Safe failure code/)).toBeInTheDocument();
  expect(screen.getByRole('button',{name:'Mark read'})).toBeInTheDocument();
});
