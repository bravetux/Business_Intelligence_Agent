# Product Discovery Notes — Saved Cards Feature

**Date:** 2026-04-25
**Workshop:** Product Discovery, Round 2
**Facilitator:** Nora Ali (Product Manager)
**Attendees:** Nora Ali (PM), Daniel Chen (Backend Lead), Vikram Shah (Frontend),
Priya Raman (SRE), Marcus Webb (Customer Support Lead), Eva Lindqvist (UX Designer).

**Goal of session:** finalise the requirements for the upcoming "saved cards" feature
so engineering can break it into stories for Sprint 28 and Sprint 29.

---

## Why we're doing this

Customer Support is seeing 60+ tickets a week from repeat customers complaining that
they have to re-enter their card details on every order. Internal data shows our
top 20% of customers place an order every 11 days on average — they're a captive
audience, and we're costing them friction. Finance approved the work last week. The
target is a measurable reduction in checkout abandonment for return customers, plus
a drop in those support tickets.

We are NOT trying to compete with full digital wallets (Apple Pay, Google Pay) — those
are already supported. This is for customers who pay by card today and want their
card remembered.

---

## Discussed requirements

### Requirement 1 — Listing saved cards at checkout

A returning customer who has previously paid by card on our site should see their
previously-used cards at the checkout step, masked (last 4 digits visible only),
with the brand (Visa, Mastercard, Amex) and the card's expiry month/year. They can
pick one with a single click. If they pick one, the card token is sent to the
backend and used to charge — no CVV re-entry, because Stripe's saved-card flow
covers that.

If a customer has never saved a card, the checkout page looks exactly like it does
today. We do not want to change the experience for first-time customers.

Eva flagged: the saved-cards UI must be accessible — keyboard navigation, screen
reader announcements for masked numbers ("Visa ending in 4 2 4 2"), and adequate
colour contrast for the selected state. Hard requirement, not nice-to-have.

### Requirement 2 — Adding a card from the profile page

From the customer's profile page, under a new "Payment methods" section, the
customer should be able to add a new card. They enter card details into a Stripe
Elements form (we don't touch raw PAN — PCI scope reasons). On success, the card
is saved against their customer record and shown in the list.

We agreed: minimum information collected is card number, expiry, CVV, and billing
postcode. No cardholder name field — Stripe doesn't need it for our merchant
category, and asking for it just adds friction.

If the card fails Stripe's validation (e.g. address mismatch), the form should
show a clear error inline — not a toast, not a redirect. Eva will design this state.

### Requirement 3 — Removing a saved card

Customers must be able to remove a saved card from their profile page. One-click
delete with a confirmation modal ("Remove this Visa ending in 4242?"). On confirm,
the card is removed from Stripe via their detach API and from our DB.

Marcus pushed back on the confirmation modal — he's seen friction-survey data
where customers complain about "are you sure" prompts. Compromise: confirmation
modal stays, but the modal copy is friendly, not alarming, and the cancel button
is the lighter visual weight.

### Requirement 4 — Card limits

A customer can save up to 5 cards. Beyond that, the "Add card" button is disabled
with tooltip text explaining the limit and suggesting they remove an existing card
first. Daniel pushed for this limit — it caps our PCI exposure and the storage
cost on Stripe's side.

### Requirement 5 — Default card selection

If a customer has multiple saved cards, the most recently used card is pre-selected
at checkout. Customers can change the selection but we don't expose a "set as
default" UI in this version. Nora wants to ship lean and add an explicit default
later if we see demand.

### Requirement 6 — Security and audit

Every save, use, and delete of a card must emit a Kafka event to the
`payments-events` topic with the customer ID, action, and timestamp. The security
team will consume those events for audit. PII (card number, even masked) must
NOT be in the event payload — only the Stripe payment-method ID.

Priya flagged: this means our existing audit-event schema needs an extension. She'll
work with the security team to confirm the schema change is OK before any code
ships.

### Requirement 7 — Mobile responsiveness

The saved-cards picker at checkout and the profile-page management screen must
work on mobile breakpoints down to 360px width. Vikram confirmed our component
library supports this; he just needs to write the styles.

### Requirement 8 — Analytics

Product wants three events tracked: `saved_card_used` at checkout, `saved_card_added`
on the profile page, `saved_card_removed` on the profile page. Each event should
include the card brand (Visa/MC/Amex) but no other card data. Nora will write the
tracking spec.

---

## Out of scope (explicitly)

- Setting a card as default (deferred — see Requirement 5).
- Sharing cards across multiple customer accounts.
- Importing cards from third-party wallets.
- Showing the full card number — never, under any circumstance.
- Saving cards for one-click checkout from order confirmation emails (separate
  initiative, not on this team's roadmap).

---

## Open questions and risks

- Legal hasn't yet confirmed whether the saved-card list needs an explicit
  consent step in EU — Nora will follow up with legal by Wednesday April 30.
- We need to decide how to handle expired cards — silently hide them, or show
  them with an "expired" badge so the customer knows to remove them. No decision
  in this session; Eva will mock both options for the next review on May 2.
- If Stripe is down at the moment a customer tries to add a card, what does the
  UX look like? Vikram and Priya will sync separately on the failure path.

---

## Sequencing agreed in the room

Sprint 28 (May 4 – May 15): Requirement 1 only — the read-only saved-cards picker
at checkout. Backend endpoint + frontend wiring.

Sprint 29 (May 18 – May 29): Requirements 2, 3, 4, 5, 6, 8 — full add/remove from
profile, limits, default selection, audit events, analytics.

Mobile responsiveness (Requirement 7) is folded into both sprints as part of each
UI task — not a separate story.
