"""Explain changes between retained snapshots without refreshing live evidence."""
from sqlalchemy import select

from app.domain.models import CaseBriefVersion
from app.research.brief_versions import view

GROUPS = ('sources', 'claim_records', 'model_observations', 'reviews', 'conclusions', 'questions', 'conflicts')


def compare_content(before, after):
    groups = {}
    for group in GROUPS:
        old = {r['id']: r for r in before[group]}
        new = {r['id']: r for r in after[group]}
        rows = []
        for key in sorted(old.keys() | new.keys()):
            left, right = old.get(key), new.get(key)
            if left == right:
                continue
            kind = 'added' if left is None else 'removed' if right is None else 'changed'
            fields = sorted(k for k in (left or {}).keys() | (right or {}).keys()
                            if k not in (left or {}) or k not in (right or {}) or left[k] != right[k])
            rows.append({'id': key, 'kind': kind, 'fields': fields, 'before': left, 'after': right})
        groups[group] = {'counts': {kind: sum(r['kind'] == kind for r in rows)
                                    for kind in ('added', 'changed', 'removed')}, 'rows': rows}
    # Counts alone miss case-level timing/fit/context changes. Compare every
    # remaining snapshot field, including unknown future fields, conservatively.
    context = [{'field': key, 'before': before.get(key), 'after': after.get(key)}
               for key in sorted((before.keys() | after.keys()) - set(GROUPS))
               if key not in before or key not in after or before[key] != after[key]]
    return {'unchanged': before == after, 'groups': groups, 'context_changes': context}


def compare(db, case_id, from_version, to_version):
    if from_version < 1 or to_version < from_version:
        raise ValueError('Choose positive versions with the earlier version first')
    rows = db.scalars(select(CaseBriefVersion).where(CaseBriefVersion.case_id == case_id,
        CaseBriefVersion.version.in_([from_version, to_version]))).all()
    versions = {row.version: row for row in rows}
    if from_version not in versions or to_version not in versions:
        raise LookupError('Both saved brief versions must exist in this case')
    before, after = versions[from_version], versions[to_version]
    return {'method': 'retained-brief-comparison-v1', 'case_id': case_id,
            'from': view(before, include_content=False), 'to': view(after, include_content=False),
            **compare_content(before.content, after.content)}
