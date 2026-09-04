# Validate optional AI summary providers

Status: proposed · Priority: P2

Problem: OpenAI and Anthropic adapters exist but have not been exercised live, and the Docker image omits optional provider SDKs.

Outcome: mock routine provider behavior, record token usage where available, make intentional Docker support explicit, and run bounded live checks only when credentials and product need justify cost. Summary output must remain labeled inference and evidence-bounded.
