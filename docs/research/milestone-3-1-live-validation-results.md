# Milestone 3.1 bounded public-case validation results

Executed September 4, 2026 against the approved seven-case manifest. This report uses case IDs and aggregate measures; the local manifest and provider outputs remain ignored. No result is an outreach recommendation or authoritative ownership decision.

## Execution record

- Seven retrospective cases: Colorado 2, Utah 2, Texas 3.
- Fourteen provider/case paths, with OpenAI `gpt-5-mini` and Anthropic `claude-sonnet-4-5` receiving the same versioned evidence packet and JSON Schema.
- First attempt: OpenAI rejected all seven requests because the validation schema included an unsupported array constraint. Anthropic returned seven responses, but prompt-only JSON was not reliably parseable. These results were not scored.
- The adapters were corrected and tested offline: the unsupported constraint was removed and Anthropic native structured outputs were enabled.
- Second/final attempt: Anthropic returned seven schema-valid results. OpenAI returned five schema-valid results and two empty/non-JSON outputs after consuming its output budget.
- No third attempt was made because the approved two-call provider/case ceiling was exhausted.

Across both attempts, Anthropic used 11,895 tokens and OpenAI used 8,918 reported tokens. Even treating every token as output at the published rates gives conservative upper bounds of approximately $0.18 and $0.02 respectively across the full cohort, below the $0.25 per-provider/case ceiling. Exact cost is not claimed because the current execution record captures total rather than separate input/output tokens.

## Outcome comparison

Only 3 of 14 provider/case paths matched the pre-labeled top-level outcome; two paths had no parseable OpenAI result. The raw exact-match rate is therefore not evidence of acceptable product quality.

| Case | Expected top-level outcome | OpenAI | Anthropic | Analyst finding |
| --- | --- | --- | --- | --- |
| DS31-01 | active owner relationship | no parseable result | former owner; business active | The output correctly separated business activity from the deceased person's now-former relationship, exposing an ambiguous expected label. |
| DS31-02 | active owner relationship | former owner; status unclear | former owner; status unclear | Both preserved the explicit relationship but correctly refused to infer current business status from a directory listing. |
| DS31-03 | former owner | match | match | Both correctly recognized the documented succession and continuing business. |
| DS31-04 | inactive business | no parseable result | former owner; business inactive | Component facts were correct, but the forced outcome could not express both conditions. |
| DS31-05 | ambiguous identity | match | business-first resolved | Anthropic's summary said the business could not be identified, contradicting its own top-level outcome. |
| DS31-06 | contradictory ownership | former owner | former owner | Both resolved the apparent conflict by respecting dates. The pre-label overstated contradiction: principal ownership transferred while a non-owner leadership title continued. |
| DS31-07 | business-first resolved | former owner | former owner | Both resolved the business/person evidence, but chose relationship state because origin and resolution were mixed into one enum. |

## Product finding

The evidence packets produced useful, source-bounded summaries, but the validation schema is not fit for broader evaluation. A single outcome enum currently conflates at least four independent dimensions:

1. case origin (`signal_first`, `business_first`, `hybrid`);
2. identity-resolution state;
3. person/business relationship and its effective dates;
4. business operating status.

Those dimensions must become separate required fields with deterministic precedence and analyst scoring rules. Provider responses must also retain separate input/output token usage and explicit incomplete/refusal status. The two OpenAI empty outputs need a bounded-output diagnostic; increasing a budget silently is not an acceptable fix.

## Closeout decision

The run validates real local provider connectivity, native structured-output integration, evidence grounding, budget enforcement, and several useful negative behaviors. It does not validate the current comparison rubric or close Milestone 3.1. The next implementation slice is a version-two multidimensional evaluation contract exercised against saved synthetic fixtures. Because the live case call ceiling has been reached, the approved public cohort will not be rerun without a new explicit protocol decision.
