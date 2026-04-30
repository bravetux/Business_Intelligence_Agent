# Sprint 28 Planning — Checkout Squad

**Date:** 2026-04-29
**Time:** 10:00 – 11:05 IST
**Location:** Zoom + Conference Room B
**Facilitator:** Aarti Joshi (EM)
**Note-taker:** Priya Raman

**Attendees:**
- Aarti Joshi (Engineering Manager)
- Daniel Chen (Backend Lead)
- Priya Raman (SRE)
- Vikram Shah (Frontend)
- Lin Zhao (Platform)
- Nora Ali (Product Manager)
- Marcus Webb (Customer Support Lead, joined for first 20 min)

**Apologies:** Sanjay Kapoor (VP Eng) — sent priorities ahead.

---

## Transcript

**Aarti:** Good morning everyone. Goal today is to lock the Sprint 28 scope. Two weeks,
starts Monday May 4th, ends Friday May 15th. Nora, you want to walk us through the
priorities Sanjay sent?

**Nora:** Sure. The top item is the new "saved cards" feature for repeat customers —
finance signed off on it yesterday. Second is finishing the refund-reason codes
migration, that one's been carried over twice now. Third is reducing checkout p95
latency below 800ms — currently hovering around 1.2 seconds.

**Daniel:** On the saved cards work — we agreed last week the scope is read-only for
this sprint, right? Just listing previously-used cards on the checkout page. Adding
new ones from the profile page is Sprint 29.

**Nora:** Correct. Read-only in 28, add/delete in 29.

**Vikram:** The frontend piece for read-only cards is roughly 3 days of work. I can
own it. I'd want the API contract finalised by end of day Tuesday so I can stub it.

**Daniel:** I'll have the contract in the shared Confluence page by EOD Tuesday May 5.

**Priya:** Quick concern — can we make sure the saved-cards endpoint goes through the
new circuit breaker pattern? After last week's Redis incident I don't want to ship
another endpoint without it.

**Daniel:** Agreed. I'll wrap it in the circuit breaker decorator. Good call.

**Marcus:** From support — we're getting roughly 40 tickets a week from customers
saying their refund didn't arrive. About half of those turn out to be the reason-code
mismatch. Whatever's left of the migration is genuinely painful for us.

**Lin:** The migration itself is mostly done. What's left is backfilling 180 days of
historical refunds with the new codes. That's a one-shot job, maybe a day of work,
plus a day of monitoring while it runs.

**Aarti:** Lin, can you own the backfill in this sprint?

**Lin:** Yes. I'll target running it on May 8 — a Friday — so we can babysit it over
the weekend if needed.

**Aarti:** Marcus, do you need anything from us on customer comms while the backfill runs?

**Marcus:** A heads-up the morning of, and a banner in the support tool saying refunds
may show stale codes for a few hours. Lin, can you ping #support-leads on Slack when
you kick it off?

**Lin:** Will do.

**Aarti:** Priya, latency reduction — what's your read?

**Priya:** I've identified three contributors. One, the address-validation call is
synchronous and adds ~280ms — I want to make it parallel with the tax calc. Two,
we're double-fetching the cart on confirmation, that's another ~150ms. Three, we
could add a 60-second cache on the country/region lookup, that's ~80ms. Combined
should comfortably get us under 800ms p95.

**Daniel:** I'd like a design doc on the parallel address+tax change before we
implement. The two services have different timeout behaviour and I want to make
sure we're not masking failures.

**Priya:** Fair. I'll draft a design doc by Wednesday May 6 and we can review Thursday.

**Aarti:** Open question — Nora, are we doing anything for the EU launch this sprint?

**Nora:** Blocker — legal still hasn't approved the Italian translation of the T&Cs.
I don't want to commit anything until that lands. I'll ping legal again Friday.

**Aarti:** OK. So that's deferred to Sprint 29 unless legal closes by next Wednesday.

**Vikram:** One more thing — Chrome 128 broke our Apple Pay button on iOS Safari
because of a CSS regression. It's not in scope but it's customer-facing. Can we
slot it in as a stretch goal?

**Aarti:** Add it as a stretch. If we have capacity end of week 1 we'll pull it in.

**Marcus:** I have to drop in 2 minutes. Anything you need from support?

**Aarti:** Just the heads-up coordination with Lin on the backfill. Thanks Marcus.

**Marcus:** [left at 10:22]

**Aarti:** Priya, on the latency work — given Daniel needs the design doc first, are
you confident this still fits in two weeks?

**Priya:** The cart double-fetch and the country cache are easy, maybe 2 days total.
The address+tax parallelisation is the chunk — 4 days including the design review.
Total should be 6 working days, fits in the sprint.

**Aarti:** OK. Decisions then — let me read these back. Sprint 28 scope: read-only
saved cards, refund-code backfill, latency reductions. EU launch deferred. Apple Pay
button is a stretch. Yes?

**[General agreement around the room.]**

**Aarti:** Daniel, I want to flag one thing. Sanjay mentioned in his note he wants
us to start thinking about the architecture for splitting the payment service into
checkout and refunds as separate services. He's not asking for a decision this
sprint, but he wants a one-pager from you by end of May. Just keep that on your radar.

**Daniel:** Noted. I'll put a calendar block for it.

**Aarti:** Anything else? Going once... going twice... thanks everyone, see you at
standup tomorrow.

**[Meeting ended 11:05.]**
