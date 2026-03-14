# Score Trust Rebalance

## Why
Explicit trust inputs currently add directly to raw score. That lets source reputation distort ranking and makes the displayed score look more absolute than it really is.

## Scope
- convert explicit trust inputs into bounded ranking priors
- store raw and adjusted scores separately
- show adjusted scores in user-facing surfaces
- rename profile wording so operators understand trust is a soft preference
- validate the design against synthetic user comprehension
