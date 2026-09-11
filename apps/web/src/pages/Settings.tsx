import {useQuery} from '@tanstack/react-query';
import {Settings as SettingsIcon} from 'lucide-react';
import {api} from '../api/client';
import {useIdentity} from '../components/AuthGate';
import {OperationalHealth,OperationalHealthResult} from '../components/OperationalHealth';

export function SettingsPage(){const identity=useIdentity();const permitted=identity?.role==='operator'||identity?.role==='administrator'||identity?.role==='demo';const health=useQuery({queryKey:['operational-readiness'],queryFn:()=>api<OperationalHealthResult>('/operations/readiness'),enabled:permitted,refetchInterval:60_000});return <><div className="page-heading compact"><div><p className="eyebrow">Pilot administration</p><h1>Settings</h1><p>Provider, database, model, and security configuration remains environment-managed.</p></div></div>{!permitted?<section className="placeholder panel"><SettingsIcon/><h2>Operator access required</h2><p>Your pilot role does not expose infrastructure, cost, failure, or audit-health details.</p></section>:health.isLoading?<section className="panel">Loading operational readiness…</section>:health.isError||!health.data?<section className="panel"><h2>Operational readiness unavailable</h2><p>The protected readiness check could not be completed.</p></section>:<OperationalHealth result={health.data}/>}</>}
