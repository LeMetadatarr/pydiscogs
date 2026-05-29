# TODO — pydiscogs

## Gaps

- [ ] No CI workflows — `.github/workflows/` is absent. Add the standard gh-automations reusable workflows (build-tests, coverage, license-check, release_workflow, publish_stable), referencing `OpenVoiceOS/gh-automations` at `@dev`. Sibling clients in this cluster ship no CI either, so there is no obvious local template to copy yet.
- [ ] No lint/typecheck config — no ruff/mypy despite full type-hint usage.

## Code TODOs

- [ ] Optional CHECKSUM verification: `bulk.checksums()` returns the index keys but does not yet fetch/parse them to validate a cached `download()`.
- [ ] Optional gated REST API supplement (`api.discogs.com`, token required) for per-record live lookups is documented but not implemented.
- [ ] `lxml` is declared as an optional extra but the parser currently always uses stdlib `xml.etree`; wire an lxml fast path when the extra is present.
- [ ] Add a real HuggingFace loading script under `dataset.py` consumers once a dataset repo exists.
