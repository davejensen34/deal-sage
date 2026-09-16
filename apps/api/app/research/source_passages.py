"""Read-only, reproducible passages from already retained source artifacts.

Offsets address normalized Unicode text, never raw HTML byte positions. Passage
selection is evidence preparation, not semantic validation or corroboration.
"""
from hashlib import sha256

from app.domain.models import CaseEvidence, RawArtifact
from app.research.html_excerpt import html_excerpt

VERSION = 'source-passages-v1'
MAX_BYTES = 1_000_000
MAX_CHARACTERS = 100_000
PASSAGE_CHARACTERS = 2_000
OVERLAP = 200
PAGE_SIZE = 10


def document(db, case_id, evidence_id, storage):
    item = db.get(CaseEvidence, evidence_id)
    if item is None or item.case_id != case_id:
        raise ValueError('Evidence not found in this case')
    artifact = db.get(RawArtifact, item.raw_artifact_id) if item.raw_artifact_id else None
    if artifact is None:
        raise ValueError('Retained artifact unavailable; use the original excerpt')
    if (artifact.content_hash != item.content_hash or artifact.canonical_url != item.canonical_url
            or not 1 <= artifact.byte_size <= MAX_BYTES):
        raise ValueError('Retained artifact does not match evidence or exceeds the byte limit')
    try:
        content = storage.read_bounded(artifact.storage_key, MAX_BYTES)
    except (OSError, ValueError):
        # Storage paths and exception bodies are not public evidence metadata.
        raise ValueError('Retained artifact unavailable or over the byte limit') from None
    if len(content) != artifact.byte_size or sha256(content).hexdigest() != item.content_hash:
        raise ValueError('Retained artifact integrity check failed')
    if artifact.media_type == 'text/html':
        text = html_excerpt(content, limit=MAX_BYTES)
    elif artifact.media_type in {'text/plain', 'application/json'}:
        text = content.decode('utf-8', errors='replace')
    else:
        raise ValueError('Retained artifact media type is unsupported')
    if not text or not text.strip():
        raise ValueError('No permitted readable source text is available')
    retained = text[:MAX_CHARACTERS]
    # Do not create a redundant final passage consisting only of overlap.
    count = 1 + max(0, (len(retained) - PASSAGE_CHARACTERS + PASSAGE_CHARACTERS - OVERLAP - 1)
                    // (PASSAGE_CHARACTERS - OVERLAP))
    metadata = {
        'version': VERSION, 'evidence_id': item.id, 'raw_artifact_id': artifact.id,
        'content_hash': item.content_hash, 'text_hash': sha256(text.encode()).hexdigest(),
        'text_characters': len(text), 'available_characters': len(retained),
        'truncated': len(retained) < len(text), 'passage_count': count,
        'passage_characters': PASSAGE_CHARACTERS, 'overlap_characters': OVERLAP,
        'offset_unit': 'normalized_unicode_characters',
    }
    return metadata, retained


def _passage(metadata, text, index):
    if type(index) is not int or not 0 <= index < metadata['passage_count']:
        raise ValueError('Passage index is outside the retained document')
    start = index * (PASSAGE_CHARACTERS - OVERLAP)
    end = min(start + PASSAGE_CHARACTERS, len(text))
    excerpt = text[start:end]
    return {'index': index, 'start': start, 'end': end, 'excerpt': excerpt,
            'excerpt_hash': sha256(excerpt.encode()).hexdigest()}


def select_passage(db, case_id, evidence_id, storage, index):
    metadata, text = document(db, case_id, evidence_id, storage)
    return metadata, _passage(metadata, text, index)


def list_passages(db, case_id, evidence_id, storage, page=1):
    if type(page) is not int or page < 1:
        raise ValueError('Passage page must be positive')
    metadata, text = document(db, case_id, evidence_id, storage)
    start = (page - 1) * PAGE_SIZE
    return {**metadata, 'page': page,
            'items': [_passage(metadata, text, i)
                      for i in range(start, min(start + PAGE_SIZE, metadata['passage_count']))],
            'has_next': start + PAGE_SIZE < metadata['passage_count']}
