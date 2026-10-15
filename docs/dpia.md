# Data protection impact assessment (DPIA)

**Draft for review. Not a legal determination.** Complete with the controller, a qualified Nigerian privacy professional, and the actual hosting providers before any live athlete data is collected.

## Processing overview

Sinopia supports coaches managing team training load and athlete self-reported wellness. Data includes coach Google account identifiers, a team identifier, athlete labels/codes, session duration and effort, and check-in scales for sleep, energy, soreness, stress, and pain area. Some check-in data is health-related and may concern children under 18.

## Purpose and necessity

The intended purpose is to help an authorised coach review workload history and notice a reason to speak with an athlete. The tool is not a diagnostic service and its thresholds are provisional. Use initials/codes and fixed-choice fields to reduce unnecessary identifiers. Do not collect date of birth, photos, phone numbers, location, or free-text medical histories.

## Risks and mitigations

| Risk | Current mitigation | Remaining work |
|---|---|---|
| Cross-team disclosure | Team IDs on player, session, and check-in records; route-level team scoping; 404 for foreign IDs | Test every route and migration; complete PostgreSQL migration |
| Link theft | Separate random check-in token, hashed token storage, token in URL fragment rather than path, coach-only regeneration, token-aware throttling | Add shared rate limiting and monitoring |
| Unauthorised coach access | Google ID token verification, server-side opaque sessions, HttpOnly cookie, policy gate | Configure real client IDs, production HTTPS, trusted origins, and Vercel first-party API rewrite |
| Child data processed without authority | Coach declaration and athlete-registration consent checkbox | Verify consent workflow, records, notice delivery, and school/club authority |
| Pain report remains unaddressed | Pain flag persists until coach acknowledgement | Define operational response expectations and audit acknowledgements |
| Excessive retention | Hard account deletion route | Implement scheduled 12-month retention and inactivity warnings |
| Provider disclosure | Generic status reasons only are sent to optional Groq explanation | Test outbound payload, confirm contracts and regions, consider disabling by default |
| Misinterpretation as medical advice | UI and terms describe outputs as provisional prompts | Independent review and validation before any health-related claim |

## Lawful basis and children

Counsel must determine the appropriate lawful basis for each processing purpose under the Nigeria Data Protection Act and applicable regulations. Confirm how consent is obtained and recorded for athletes under 18, what notice is delivered to the athlete, and how withdrawal is handled. The age checkbox is a declaration, not independent age verification.

## Decisions required before launch

- Confirm controller legal identity and privacy contact.
- Confirm lawful basis and parent/guardian consent process.
- Confirm all providers, subprocessors, processing regions, and cross-border transfer safeguards.
- Complete a data retention and backup-expiry schedule.
- Test hard deletion across every table and backup policy.
- Complete threat modelling, independent security review, and deployment configuration review.
- Review this DPIA with a qualified privacy lawyer and document approval.
