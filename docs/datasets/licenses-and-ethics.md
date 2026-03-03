# Licenses and Ethics

## Licensing Summary
- O*NET data: verify attribution/license details on O*NET release pages (currently published with reuse terms; check release notes each update).
  - Source: https://www.onetcenter.org/database.html
  - Accessed: 2026-03-03
  - Version: O*NET 30.0 page context
- USAJOBS API: governed by official developer terms/usage requirements.
  - Source: https://developer.usajobs.gov/
  - Accessed: 2026-03-03
  - Version: N/A
- US government datasets (Census/BLS/OPM): generally public data; still review dataset-specific notices before redistribution.

## PII and Sensitive Data Rules
- Do not publish raw documents or enriched chunks that contain personal contact details.
- Preserve source lineage to support deletion/rectification workflows where applicable.
- Add redaction hooks before chunking/indexing text.

## Practical Guardrails
- Keep raw text in object storage/lake, not in wide graph properties.
- Store only references (`source_uri`, `doc_id`) and concise summaries in graph unless needed.
- Tag every derived artifact with extraction and model version metadata.

## Official Sources
- NIST SP 800-122 (PII confidentiality guidance): https://csrc.nist.gov/pubs/sp/800/122/final (Accessed: 2026-03-03, Version: Final)
- NIST Privacy Framework: https://www.nist.gov/privacy-framework (Accessed: 2026-03-03, Version: 1.1)
