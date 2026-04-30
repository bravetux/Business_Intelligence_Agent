# KT Session — Payment Service Onboarding

**Date:** 2026-04-22
**Duration:** 90 minutes
**Presenter:** Daniel Chen (Backend Lead, payment-service, 4 years on the team)
**Audience:** Rohan Patel (new senior engineer, joining payment-service squad next week)
**Format:** Live walk-through over Zoom, screen-shared. Notes captured by Priya Raman.

---

## Opening — why this session exists

Rohan is joining the checkout squad on May 6. He's owned billing systems before but
not this specific codebase. The goal of this KT is to get him to a point where, on
day one, he can read an alert, find the relevant code, deploy a fix, and roll it back
if needed. Not to make him an expert — just unblock him.

---

## What payment-service actually is

Payment-service is the Python (FastAPI) backend that handles two top-level customer
flows: **checkout** (charging a card to complete an order) and **refunds** (returning
money for a returned order). It does not handle subscriptions — that's a separate
service called `billing-recurring`. It does not handle fraud scoring — that's
`risk-engine`, a synchronous dependency.

The service is owned by the checkout squad: Daniel (lead), two backend engineers,
and rotating SRE coverage from Priya's team.

It runs in Kubernetes namespace `payments`, in the `prod-eu-west` and `prod-us-east`
clusters. About 8 pods per cluster under normal load, scaling to 20 during peak hours.

---

## Architecture in one breath

A request comes in through the API gateway, hits an authentication middleware that
validates a JWT, then routes to one of two FastAPI routers — `/v2/checkout/*` or
`/v2/refunds/*`. Each router calls one or more downstream dependencies:

- **PostgreSQL** (`payments-prod-pg`) — orders, transactions, refund records.
  Connection pooling via SQLAlchemy with a per-pod cap of 30 connections.
- **Redis** (`redis-payments-prod`) — idempotency keys, short-lived locks, cached
  card metadata. Pool cap of 200 per pod.
- **Stripe** (external, the payment processor) — actual money movement.
- **risk-engine** (internal) — fraud scoring, blocks the request path. 200ms budget.
- **Kafka** (`payments-events` topic) — emits domain events for downstream consumers
  (analytics, ledger, customer notifications).

The most important file to know is `src/payment_service/checkout/confirm.py`. That's
the hot path for the checkout flow — every order charge funnels through it. If you
only learn one file, learn that one.

---

## Key components, in priority order for a new engineer

### 1. The confirm-checkout flow (`checkout/confirm.py`)

- Takes an order ID and a payment method token.
- Acquires a Redis idempotency lock keyed on order ID — this is what stops double-charges
  if the customer hits "pay" twice.
- Calls risk-engine for a fraud score. Anything above 80 is blocked outright.
- Calls Stripe to charge the card. This is the only network call that can cost money,
  so it has aggressive retry logic with exponential backoff up to 3 attempts.
- On success, writes a `transactions` row and emits a `checkout.completed` Kafka event.
- On Stripe failure, writes a `transactions` row with status `failed` so the customer
  can retry. Does NOT emit an event in that case.

### 2. The refund handler (`refunds/process.py`)

- Looks up the original transaction.
- Calls Stripe's refund API.
- Writes a `refunds` row and emits a `refund.completed` event.
- Has a known quirk: if the original transaction was processed before our
  reason-codes migration in Q1 2026, the refund record uses an empty reason code.
  The migration backfill is being run by Lin in Sprint 28 to fix that.

### 3. The circuit breaker wrapper (`common/circuit.py`)

- All outbound HTTP calls (Stripe, risk-engine) go through this.
- Breaks after 5 consecutive failures, stays open for 30 seconds, then half-opens to
  test recovery. Standard pattern, nothing custom.
- New endpoints **must** use this — see the team's recent post-incident decision.

### 4. The idempotency layer (`common/idempotency.py`)

- Wraps Redis SET NX with a TTL of 24 hours.
- The key is namespaced as `idem:checkout:{order_id}`.
- If you find yourself wanting to bypass this for testing, **don't** — use the test
  fixtures that mock out Redis instead. Bypassing in real code has caused at least
  two incidents in the last year.

---

## How to make a change — step by step

1. **Branch off main.** Naming convention: `feature/CHECKOUT-1234-short-description`
   or `fix/CHECKOUT-1234-short-description`. The Jira key prefix is required so the
   merge bot links the PR back.
2. **Write or update tests first** — the team enforces this in code review. The test
   suite for payment-service lives in `tests/payment_service/` and runs with
   `pytest tests/payment_service/`. Integration tests need a local Postgres and Redis;
   `make test-integration-up` spins those up via docker-compose.
3. **Run the linter** — `make lint`. We use ruff and mypy. Mypy is on strict mode
   for this service; expect it to be picky.
4. **Open a PR.** Two reviewers required, one of whom must be from the checkout squad.
   For changes touching `confirm.py` or `circuit.py`, Daniel must be one of the two.
5. **Wait for CI.** The full CI takes about 12 minutes. Don't skip it.
6. **Merge.** The merge bot squashes commits. Write the PR title carefully — that
   becomes the commit message.
7. **Watch the deploy.** Auto-deploy to staging happens within 2 minutes. Production
   is a manual click via Spinnaker, behind a canary that rolls 1 pod → 25% → 100%
   over 20 minutes. Never skip the canary.

---

## Known issues and gotchas

- **Healthcheck doesn't touch Redis.** This means a pod with a dead Redis pool can
  stay "healthy" from Kubernetes' perspective and continue receiving traffic.
  There's a follow-up ticket to add a deeper healthcheck — Daniel owns it, due
  May 12.

- **The `confirm.py` retry loop has bitten us.** If you change anything in the retry
  block, run the leak test (`tests/payment_service/test_confirm_leak.py`). This is
  the regression test from the April 28 Redis pool exhaustion incident.

- **Stripe sandbox keys rotate every 90 days.** They live in 1Password under
  `payments-stripe-sandbox`. If your local tests start failing with 401s, that's
  almost always the cause.

- **Datadog APM is the source of truth for prod debugging,** not application logs.
  Logs are noisy. Filter Datadog by `service:payment-service env:prod` and pivot
  on the `trace_id`.

- **Don't run database migrations during business hours.** Even "safe" migrations
  have surprised us. The unspoken rule is migrations after 22:00 IST or on weekends.

- **The Kafka producer is fire-and-forget by design.** If you need a synchronous
  guarantee that an event was emitted, you're using the wrong tool — write to the
  outbox table instead, the relay job will pick it up.

---

## Where to look when things break

- **Datadog APM:** `app.datadoghq.com/apm/services/payment-service`
- **Datadog dashboards:** the bookmarked one is `payment-overview`, plus
  `payment-redis` and `payment-stripe`.
- **Logs:** Datadog log explorer, filter on `service:payment-service`.
- **PagerDuty schedule:** `sre-payments-primary` and `sre-payments-secondary`.
- **Runbook:** Confluence space `RB`, page "payment-service".
- **Incident channel template:** `#inc-{date}-{nnn}`.
- **Code:** repo `github.com/acme/payment-service`, default branch `main`.

---

## References Daniel called out

- The Stripe API docs are the spec of truth for any payment-method behaviour —
  do not guess from our wrappers.
- Internal RFC `RFC-0042` ("idempotency at the edge") explains the design choices
  in `idempotency.py`. Worth reading on day one.
- The post-incident review for INC-20260428-014 (Redis pool exhaustion) is the
  best single document for understanding why the team is so strict about the
  circuit breaker pattern.
- Onboarding checklist in Notion: "Checkout squad — first 30 days".

---

## Closing — Daniel's advice

"Don't be afraid to ask before deploying. Nobody on this team gets annoyed by a
pre-deploy sanity check. They get annoyed when a customer-facing incident could
have been avoided by one. Push to staging early, watch the dashboards, and treat
production deploys like a small ceremony, not a chore."
