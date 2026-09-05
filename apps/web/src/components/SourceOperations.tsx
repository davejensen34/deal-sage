import {AlertTriangle, CheckCircle2, Database, ShieldX} from 'lucide-react';

export type SourceSample = {
  source_key: string;
  jurisdiction: string;
  sample_kind?: string;
  live_source_exercised?: boolean;
  retrieved: number;
  curated: number;
  quarantined: number;
  field_completeness_percent?: number;
  relationship_assertions?: number;
  ownership_supported_assertions?: number;
  explicit_owner_role_assertions?: number;
  control_role_candidate_assertions?: number;
  role_counts?: Record<string, number>;
  repeat_verified?: boolean;
  retrieval_latency_ms?: number;
  marginal_cost_usd: number;
  freshness?: {status: string; reason: string};
  next_action?: string;
};

export type SourceDecision = {
  source_key: string;
  coverage: string;
  status: string;
  reason: string;
};

export type SourceSampleResult = {
  contains_record_level_data: boolean;
  sources: SourceSample[];
  decisions: SourceDecision[];
};

const label = (value: string) => value.replaceAll('_', ' ');

export function SourceOperations({result}: {result: SourceSampleResult}) {
  return <section className="panel source-operations">
    <div className="panel-title">
      <div>
        <p className="eyebrow">Milestone 3 · source operations</p>
        <h2>Multi-state evidence landing</h2>
        <p>Aggregate health only. Raw records and personal identifiers stay out of this view.</p>
      </div>
      <span>{result.contains_record_level_data ? 'unsafe detail' : 'aggregate only'}</span>
    </div>
    <div className="source-operation-grid">
      {result.sources.map(source => {
        const isFixture = source.sample_kind === 'fictional_contract_fixture';
        const healthy = source.quarantined === 0;
        return <article key={source.source_key}>
          <div className="source-operation-head">
            {healthy ? <CheckCircle2/> : <AlertTriangle/>}
            <div><b>{source.jurisdiction}</b><span>{label(source.source_key)}</span></div>
            <i className={isFixture ? 'fixture' : 'live'}>{isFixture ? 'fixture' : 'live'}</i>
          </div>
          <dl>
            <dt>Retrieved</dt><dd>{source.retrieved}</dd>
            <dt>Curated</dt><dd>{source.curated}</dd>
            <dt>Quarantined</dt><dd>{source.quarantined}</dd>
            <dt>Field completeness</dt><dd>{source.field_completeness_percent ?? 'not measured'}{source.field_completeness_percent !== undefined && '%'}</dd>
            <dt>Relationship evidence</dt><dd>{source.relationship_assertions ?? 'fixture only'}</dd>
            <dt>Explicit owner roles</dt><dd>{source.explicit_owner_role_assertions ?? 'not measured'}</dd>
            <dt>Ownership supported</dt><dd>{source.ownership_supported_assertions ?? 0}</dd>
            <dt>Marginal cost</dt><dd>${source.marginal_cost_usd}</dd>
          </dl>
          {source.role_counts && <p><Database/> Roles: {Object.entries(source.role_counts).map(([role,count])=>`${role} ${count}`).join(' · ')}</p>}
          {source.repeat_verified && <p><CheckCircle2/> Identical delivery replay verified</p>}
          {source.freshness && <p><Database/> Freshness: {label(source.freshness.status)}</p>}
          {source.next_action && <p><AlertTriangle/> {source.next_action}</p>}
        </article>;
      })}
    </div>
    {result.decisions.map(decision => <div className="source-rejection" key={decision.source_key}>
      <ShieldX/>
      <div><b>{label(decision.source_key)} · {decision.status}</b><p>{decision.reason}</p><small>{decision.coverage}</small></div>
    </div>)}
  </section>;
}
