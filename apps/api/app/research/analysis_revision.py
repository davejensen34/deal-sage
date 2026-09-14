"""Prepare the next evaluation without changing the historical frozen bundle."""

from copy import deepcopy
from hashlib import sha256

from app.research.analysis_preparation import canonical_bytes
from app.research.observation_contract import VERSION, INSTRUCTIONS, OBSERVATION_SCHEMA


LEGACY_BUNDLE_SHA256 = "5142f997f0f29192f8ca9bd4b47e68b4532ce3e611aa4d1bea5aceecfcaeb08e"
PROTOCOL_V3 = "m7-analysis-execution-v3"
MAX_OUTPUT_TOKENS_V3 = 6000


def revise_bundle(legacy: dict) -> dict:
    """Replace only model instructions/schema/output cap after evidence verification.

    The original sources, assessment date and separate expectations are preserved.
    This is preparation, never authorization or a modification of prior results.
    """
    if sha256(canonical_bytes(legacy)).hexdigest() != LEGACY_BUNDLE_SHA256:
        raise ValueError("Legacy bundle does not match the reviewed source packets")
    bundle = deepcopy(legacy)
    bundle.update(protocol="m7-analysis-preparation-v2", execution_protocol=PROTOCOL_V3,
                  observation_contract=VERSION, supersedes_bundle_sha256=LEGACY_BUNDLE_SHA256,
                  approval_status="not_authorized", live_execution_implemented=True)
    bundle["limits"]["max_output_tokens_per_call"] = MAX_OUTPUT_TOKENS_V3
    for packet in bundle["requests"]:
        request = packet["request"]
        request["instructions"] = INSTRUCTIONS
        request["max_output_tokens"] = MAX_OUTPUT_TOKENS_V3
        request["text"]["format"].update(name="m7_observation_v2", schema=deepcopy(OBSERVATION_SCHEMA))
        encoded = canonical_bytes(request)
        if len(encoded) > 16000:
            raise ValueError("Revised request exceeds preparation byte ceiling")
        packet["request_sha256"] = sha256(encoded).hexdigest()
    return bundle
