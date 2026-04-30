# Incident Postmortem Meeting — Payment Service Outage

**Date:** 2026-04-28
**Time:** 14:00 – 14:55 IST
**Severity:** SEV-2
**Incident ID:** INC-20260428-014
**Service Affected:** payment-service (checkout & refunds API)
**Customer Impact:** ~37 minutes of elevated checkout failures; 4.2% of transactions failed between 11:18 and 11:55 IST.

**Attendees:**
- Priya Raman (SRE, on-call)
- Daniel Chen (Backend Lead, payment-service)
- Aarti Joshi (Engineering Manager)
- Marcus Webb (Customer Support Lead)
- Lin Zhao (Platform / Redis owner)

---

## 1. What happened

At 11:18 IST, the checkout API started returning HTTP 503 for a growing share of requests.
By 11:30 IST, error rate on `POST /v2/checkout/confirm` peaked at 14%.
The pattern was intermittent — some pods served traffic normally while others timed out
on every request. Refund endpoints showed the same symptom about 3 minutes later.

Root cause: the Redis connection pool in payment-service was exhausted. A change
deployed the previous evening (build `payment-service:2026.04.27-r3`) introduced a code
path that acquired a Redis connection inside a retry loop but did not release it on the
non-200 branch. Under steady traffic the leaked connections accumulated until the pool
hit its hard cap of 200 per pod.

---

## 2. How we noticed

- **Datadog monitor "payment-checkout-error-rate-5m"** paged at 11:21 IST when error rate
  crossed the 2% threshold for 3 consecutive minutes.
- Customer Support saw a spike of "Payment failed, please try again" tickets in Zendesk
  around 11:25 IST — Marcus pinged the #incidents Slack channel.
- The Grafana board `grafana.internal/d/payment-redis` showed `redis_pool_in_use` flat-
  lined at 200 (the cap) on three of the eight pods.
- Healthcheck endpoint `/healthz` kept returning 200 because it didn't touch Redis,
  so Kubernetes did not restart the bad pods on its own.

---

## 3. What we did to investigate

1. Priya acknowledged the page and opened the incident channel `#inc-20260428-014`.
2. She pulled up the Datadog dashboard and confirmed the error rate spike was scoped
   to payment-service, not upstream gateways.
3. She ran `kubectl get pods -n payments -l app=payment-service -o wide` and checked
   the per-pod request error rate in Datadog APM — three pods (`-7c9f`, `-7c9f-2`,
   `-jx4n`) were at 100% error, the rest healthy.
4. Daniel pulled the recent deploy history with `kubectl rollout history deploy/payment-service -n payments`
   and confirmed `2026.04.27-r3` had gone out at 22:40 IST the previous night.
5. Lin checked the Redis cluster (`redis-payments-prod`) — Redis itself was healthy,
   CPU ~12%, no slow-log entries, no evictions.
6. Daniel tailed application logs on a failing pod (`kubectl logs payment-service-7c9f -n payments --tail=500`)
   and saw a flood of `redis.exceptions.ConnectionError: max number of clients reached`.
7. He cross-referenced the metric `app.redis.pool.in_use{pod=~"payment-service-.*"}` in
   Datadog and confirmed the leak pattern — the bad pods climbed steadily from 11:00
   until they capped at 200.

---

## 4. What we did to fix it

1. **Mitigation (11:48 IST):** Daniel reverted the deploy with
   `kubectl rollout undo deploy/payment-service -n payments`. Pods replaced over the
   next 4 minutes and error rate returned to baseline by 11:55 IST.
2. **Verification:** Priya watched the Datadog error-rate graph for 10 minutes and
   confirmed it stayed below 0.3%. She also re-ran the synthetic checkout monitor
   manually — passed.
3. **Cleanup:** Lin confirmed Redis client count on the cluster fell back to ~80 across
   all pods, well under the cap.
4. **Permanent fix:** Daniel opened PR #4821 the same afternoon, wrapping the Redis
   acquire in a `try/finally` and adding a unit test that asserts the connection is
   returned on the error path. PR merged at 17:10 IST and rolled to prod at 18:30 IST
   behind the canary.

---

## 5. Escalation path discussion

The team agreed the escalation order for any future payment-service SEV-2 should be:

1. Primary on-call SRE (PagerDuty schedule `sre-payments-primary`).
2. Secondary on-call SRE if no ack in 5 minutes.
3. Backend Lead for payment-service (currently Daniel Chen).
4. Engineering Manager (Aarti Joshi) — for customer-facing comms or if mitigation
   takes longer than 30 minutes.
5. VP Engineering (Sanjay Kapoor) — only if customer impact exceeds 1 hour or revenue
   loss estimate exceeds $50k.

Customer Support (Marcus's team) should be looped in via the `#incidents` Slack channel
as soon as the incident is acknowledged, not after mitigation.

---

## 6. Detection criteria we want codified

We want the runbook to make it obvious how someone fresh to on-call would detect
this class of issue:

- Datadog monitor `payment-checkout-error-rate-5m` paging (>2% errors for 3m).
- Per-pod error rate divergence — some pods at 100% errors while others are clean.
- `redis_pool_in_use` metric flat at the pool cap (currently 200) on any pod.
- `redis.exceptions.ConnectionError: max number of clients reached` in app logs.
- `/healthz` continuing to return 200 despite the pod being effectively dead — this
  is a known gap; see follow-up item below.

---

## 7. Follow-up actions

| # | Action | Owner | Due |
|---|--------|-------|-----|
| 1 | File incident report in Confluence space `INC` within 24 hours | Priya | 2026-04-29 |
| 2 | Add a deep healthcheck that exercises Redis so K8s restarts dead pods | Daniel | 2026-05-12 |
| 3 | Add a Datadog monitor on `redis_pool_in_use > 180` per pod | Lin | 2026-05-05 |
| 4 | Update on-call training doc with the divergent-per-pod-errors pattern | Priya | 2026-05-15 |
| 5 | Audit other services using the same Redis client wrapper for the same leak | Daniel | 2026-05-20 |

---

## 8. Notes for the runbook

Daniel asked that the runbook include the **exact** mitigation command
(`kubectl rollout undo deploy/payment-service -n payments`) and a reminder that
reverting is the preferred first move for any payment-service regression discovered
within 24 hours of a deploy — debugging in prod under customer impact is not the goal.

Aarti added: post-incident, we always file the report within 24h, schedule a blameless
review within 5 business days, and update this runbook with anything we learned.
