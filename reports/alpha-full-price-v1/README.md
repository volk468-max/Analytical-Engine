# Alpha Full signed price experiment — 2026-11-20

## Contract

59 requested portfolio positions x10/30 XNYS sessions =118 immutable forecasts.
Six separate SPY/QQQ/SOXX outputs are not stock labels. Core display preserves
ANET,NVDA,AMD,CRWD,AVGO,GOOG,GS,META,MU,LRCX. NBIS is expanded research only;
old516-row CSV and HIST/REGIME histories/contracts remain unchanged.

The target is split-only terminal close price return, excluding dividends,
not intrahorizon DOWN TOUCH. There is no calibrated certainty/accuracy claim.
Technical pooled ridge heads train on causal mature historical price labels;
vendor revisions are explicitly NOT point-in-time history. Date weights sum1.
Missing indicators distinguish unavailable inputs from observed neutral values.
Monthly fundamentals and daily analyst assessments are signed features;
LLM macro/sector/company features and optional Seeking numeric fields preserve
actual timestamps and source hashes. No new paid feed entitlement is assumed.
Expert context priors are marked untrained. Context updates require20 distinct
mature prospective sessions, shrink toward priors, and are experimental.
Overlapping10/30 targets are dependent;20 dates are not qualification evidence.
Engineering caps and empirical residual bands are not calibrated intervals.

## Isolation, provenance and retention

Each instrument collects independently; failure/short history/stale data affects
that instrument, not all59. A missing market proxy leaves masked features.
STRIP/SCZM require a fresh verified exact provider identity; no ticker guessing.
B current-entity history begins2025-05-09; NBIS2024-10-21, avoiding older entities.
Raw licensed prices remain in the encrypted expiring payload plane. Only derived
returns/features/reference hashes are in immutable forecast/outcome journals.
No raw anchor prices are archived in forecast exports. AdditiveSQL012 changes
no former model tables. First observed outcomes are immutable; vendor correction
revision handling remains an open engineering item. Market outcomes are not yet
part of the portfolio118 training/evaluation journal.

## Daily chain (Moscow)

00:00 market/news task;02:00 company analysis, monthly baseline plus daily ratings,
revisions/mail alerts;04:00 same company task assembles separate10/30 coefficients
and source bundle, refreshes late information, delivers before04:50. Research
Railway cron remains05:00 Tue-Sat.05:30 existing private Drive export/report task
retains original516 CSV and adds independent Alpha Full price artifact handling.
On Sunday00:00 market task also prepares weekly mature-outcome/error analysis.
Five active automation slots are used; no duplicate sixth task was created.
Each task must flag unavailable sources and delivery failures. Configuration
is not proof of first real data delivery, model consumption or forecast issuance.
A first successful post-close cron with archived source provenance is required.

## Evaluation and learning

Append-only predictions, actual issued UTC, input vectors, model/weight hashes,
source availability, contributions and mature observed returns. Weekly evaluation
separates matured/pending/unresolved/blocked; reports MAE/RMSE percentage points,
direction with0.25pp deadband and strict sign, empirical band coverage, matched
technical-only and zero-return errors. Up to20 recent largest actual errors carry
saved input/contribution provenance for LLM review, not causal proof. Proposed
weight/model changes need chronological out-of-sample evaluation before promotion.

## Validation and operational checkpoint

90 relevant tests passed on native disposable PostgreSQL16.2 with0skips before
the final guarded optional-identity/error-case output edits; those are separately
rechecked before release. Parent database regression247 passed; baseline SQL
001-011 unchanged. Six-schema dump/restore verifies exact derived archive hashes.
Online knowledge validation is attempted; network failure is reported separately.
No backfill/trade/production/merge/API purchase or secret access is part of this work.

Observed Railway before this price publication: PR46 risk prototype pin
4304b731a33b0115fbd197d6ae8bd7602d35ea63, deployment
38359e4d-e7a0-4dbf-97e8-78c58aaef359 SUCCESS. This is not price deployment proof.
