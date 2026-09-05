import {render, screen} from '@testing-library/react';
import {describe, expect, it} from 'vitest';
import {SourceOperations, SourceSampleResult} from './SourceOperations';

const result: SourceSampleResult = {
  contains_record_level_data: false,
  sources: [
    {
      source_key: 'texas_active_taxpayers',
      jurisdiction: 'Texas',
      retrieved: 10,
      curated: 10,
      quarantined: 0,
      field_completeness_percent: 85.6,
      relationship_assertions: 0,
      ownership_supported_assertions: 0,
      marginal_cost_usd: 0,
    },
    {
      source_key: 'utah_bel',
      jurisdiction: 'Utah',
      sample_kind: 'fictional_contract_fixture',
      live_source_exercised: false,
      retrieved: 0,
      curated: 3,
      quarantined: 0,
      marginal_cost_usd: 0,
      next_action: 'Approval required before purchase.',
    },
    {
      source_key: 'utah_bel_live',
      jurisdiction: 'Utah',
      sample_kind: 'live_bounded_purchase',
      live_source_exercised: true,
      retrieved: 188,
      curated: 658,
      quarantined: 0,
      relationship_assertions: 470,
      explicit_owner_role_assertions: 205,
      ownership_supported_assertions: 0,
      role_counts: {Applicant: 77, Owner: 205, 'Registered Agent': 188},
      repeat_verified: true,
      marginal_cost_usd: 5,
    },
  ],
  decisions: [{source_key: 'unsafe_signal_source', coverage: 'All states', status: 'rejected', reason: 'Capability fields were exposed.'}],
};

describe('SourceOperations', () => {
  it('distinguishes live evidence, fixtures, and rejected sources', () => {
    render(<SourceOperations result={result}/>);
    expect(screen.getByText('aggregate only')).toBeInTheDocument();
    expect(screen.getAllByText('live')).toHaveLength(2);
    expect(screen.getByText('fixture')).toBeInTheDocument();
    expect(screen.getByText('unsafe signal source · rejected')).toBeInTheDocument();
    expect(screen.getByText('Roles: Applicant 77 · Owner 205 · Registered Agent 188')).toBeInTheDocument();
    expect(screen.getByText('Identical delivery replay verified')).toBeInTheDocument();
    expect(screen.getAllByText('0').length).toBeGreaterThan(0);
  });
});
