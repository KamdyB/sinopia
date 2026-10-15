# Play Store and release privacy checklist

**Release checklist. Do not submit until every applicable item is verified.**

- [ ] Target audience is set to adults (18+) and the product is not designed for children; confirm Google Play's actual target-audience and Families policy requirements.
- [ ] Complete the Data safety form from the deployed app's real data flows, including Google sign-in, coach email, training records, wellness and pain check-ins, exports, and any subprocessors.
- [ ] Publish the reviewed privacy policy at a stable public HTTPS URL and link it in the Play Console, app footer, landing footer, and check-in page.
- [ ] Publish the public account/data deletion page and test the in-app hard deletion flow with a fresh Google sign-in.
- [ ] Confirm whether Google Play's Health apps declaration applies to the final feature set; do not assume it is exempt because the app is not a medical device.
- [ ] Configure Google OAuth consent screen with the reviewed privacy and terms URLs; verify authorised domains and production client ID.
- [ ] Verify the production /api rewrite to the backend so session cookies remain first-party. Confirm Secure, HttpOnly, SameSite, CSRF, and Origin behaviour over HTTPS.
- [ ] Verify no third-party script, analytics, ads, or tracking requests occur on the athlete check-in page.
- [ ] Confirm actual provider list, data-processing agreements, processing regions, backup retention, and transfer safeguards.
- [ ] Verify data export is scoped to one team and hard deletion removes all active records and sessions.
- [ ] Run dependency and secret scans, API authorization tests, privacy review, and an independent security review.
- [ ] Replace all draft legal placeholders and obtain qualified legal review before collecting real athlete data.
