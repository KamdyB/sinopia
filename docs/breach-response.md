# Data breach response plan

**Draft operational procedure.** The controller and incident lead must be named before launch.

## 1. Detect and report

Treat suspected unauthorised access, lost check-in links, exposed credentials, unexpected exports, database exposure, and provider alerts as incidents. Record the time discovered, reporter, affected service, and evidence location. Do not put athlete names, tokens, or pain areas in general incident chat or public issue trackers.

## 2. Contain

- Revoke affected coach sessions and regenerate compromised check-in tokens.
- Disable the affected API route, provider integration, or deployment if containment requires it.
- Rotate exposed secrets and encryption keys according to the key-rotation plan.
- Preserve relevant logs and evidence with access restricted to the incident team.
- Do not destroy evidence while attempting to clean up the incident.

## 3. Assess impact

Determine the data and systems affected, whether children or health-related check-ins are involved, the number of people affected, access duration, possible copying or misuse, and whether backups or subprocessors are involved. Document facts separately from assumptions.

## 4. Notify

The controller must assess applicable legal notification duties promptly. Notify the Nigeria Data Protection Commission and affected people within applicable statutory deadlines, including the 72-hour period where required by law. If a processor is involved, follow its contract and escalation procedure. Do not use a blanket statement that every incident has the same notification deadline.

## 5. Recover and communicate

Fix the cause, rotate credentials, restore from verified clean backups if needed, validate access controls, and monitor for recurrence. Communicate what happened, what information was involved, actions taken, and practical steps affected people can take. Do not disclose other athletes' identities.

## 6. Record and improve

Maintain a restricted incident record containing the timeline, decisions, notifications, evidence references, root cause, corrective actions, and owner for each follow-up. Review this plan after exercises and real incidents.

## Before launch

Assign a named incident lead and deputy, publish a monitored privacy/security contact, define provider escalation contacts, verify backup access, and run a tabletop exercise.
