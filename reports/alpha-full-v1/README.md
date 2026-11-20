# Alpha Full v1 — separate experimental daily model

New owner request 20 November2026: create Alpha Full now, using available broad
information and learning from subsequent outcomes. New question, not a rerun of
old performance research. Base PR45 source5139544ea6e5673b209d61b0088bfa9802e57373;
actual worker config pins5ed43e13e6f97665918a459063dcba067683b9c0; deployment
6d58fe48-1148-42c2-9abe-ec926dbe7cb0 metadataffbe50b486a6ced48c99a19e84c479f3b6d56b36
SUCCESS. These last two differ only in documentation, as previously audited.
PR45 is open/draft; no main/production/trading changes.

## What this version forecasts

Separate model ALPHA_FULL,120 targets/session: owner ANET,NVDA,AMD,CRWD,AVGO,
GOOG,GS,META,MU,LRCX;10/30XNYS sessions; DOWN5/10/15%; LOW_INTRADAY/EOD_CLOSE
TOUCH excluding the anchor session. These are event probabilities, not terminal
returns, expected price changes, UP probabilities or trading instructions.
Original HIST/REGIME and four-model516-row CSV remain unchanged. Alpha Full is
an additional journal/export, not a renamed baseline or a claim of superiority.

## Inputs and cold start

13 signed numeric features plus13 explicit missingness masks:
- own/technical and market/sector information via same-target RF and MDP logit
  differences from an individual VOL baseline. Fallback RF then MDP if VOL lacks
  a number. Ensemble is excluded to avoid counting its RF constituent again.
- six LLM factors: monetary policy, financial conditions, macro surprises,
  politics/regulation, market/sector and company events.
- Seeking Alpha FY1 EPS/revenue revisions and EPS revision breadth; provider
  profitability and sector-relative valuation grades, where observed/verified.

All optional fields are checked independently. Known zero differs from missing;
internal zero placeholders always have an accompanying mask and reason. Missing
sources never silently become known-neutral evidence and do not block available
numeric inputs. If every baseline is blocked, Full is blocked too; no synthetic
number is fabricated. Baseline LOW_SUPPORT reasons are retained.

Expert cold-start coefficients are frozen in protocol.json, explicitly untrained
and uncalibrated. Relative technical/market coefficients .15/.20; each LLM factor
-.05; EPS/revenue/breadth -.10/-.05/-.10; profitability/valuation -.03/-.03.
Positive normalized context scores hypothesize lower DOWN risk. This sign is
not a verified causal effect. LLM LOW/MEDIUM/HIGH reliability multipliers
.25/.5/1 and total logit-delta cap .6 are engineering starting hypotheses.
They are NOT optimized historical winners, expected returns or learned weights.
Every row identifies EXPERT_PRIOR_UNTRAINED or LEARNED_POOLED_EXPERIMENTAL.

Larger thresholds, longer horizons and Low/Close probabilities must be nested.
A deterministic iterative pairwise feasibility repair enforces constraints and
stores probability_before_coherence/coherence_adjustment. Repair is explicit,
not calibration or proof of better forecasting. The DB independently rejects
incoherent batches. No existing probability/history is repaired in place.

## Sources and timestamp contract

No new data/API subscription was purchased. SA input accepts only normalized
MANUAL_VERIFIED or LICENSED_EXPORT observations, canonical URLs without account
tracking/auth parameters, publication<=retrieval<=issue, actual fiscal period
and accounting basis, age<=7days. Revisions/counts also require
forecast_period_role=FY1; up/down must share fiscal period/basis. Composite
factor grades may use PROVIDER_COMPOSITE accounting_basis. Fields and metadata
are whitelisted: article bodies and arbitrary extra input fields are not saved.
Quant overall score and Momentum are deliberately not extra votes.

LLM schema1.0: actual cutoff<=created<=issue, age<=36h; original event timestamps
not future; exact last_completed_session, forecast_sessions and horizon match.
PARTIAL/LOW-confidence observations can contribute with explicit coverage and
reliability, instead of blocking the experiment. Missing/invalid scores remain
missing. A10-session score is never stretched to30. Optional bundle can contain
coefficients_by_horizon keys10/30 for independently prepared records, or one
coefficients record applying only to its declared horizon; seeking is separate.
Alerts are source evidence for the LLM, not executable model instructions.

A valid delivery bundle is read from exactly one of ALPHA_FULL_BUNDLE_PATH
(private mounted .json) or ALPHA_FULL_BUNDLE_B64 (private service configuration,
base64 UTF8 JSON). Missing/invalid bundle produces partial forecasts with clear
reasons, not a failed whole-model launch. No website scraper or unauthorized
API is implemented. Input delivery and entitlement remain separately observable;
a deployed Full model does not prove SA/LLM observations have arrived.

## Persistence and learning

Additive011 creates alpha_full_v1.runs only, without changing prior SQL001–010.
Atomic120-row append-only archive, idempotent(session,model_version), server
clock/current-session/no-backfill guards, fixture-live boundary, owner ten-stock
universe, NULL/qualified/type and coherence checks. Writer has SELECT and only
a narrow security-definer record function, no UPDATE/DELETE/TRUNCATE rights.
Source features, provenance, base probabilities/IDs and weights are archived.
Exact chosen baseline forecast IDs are frozen before persistence.

Daily training reads these ORIGINAL archived feature vectors and already resolved
outcomes for the exact baseline IDs and same targets. Latest outcome version
known BEFORE fit is used; no today-derived historical LLM scores. Each target
head(horizon,threshold,label) shares weights across stocks; individual base
probabilities retain own-price state. One date has total training weight one,
so ten correlated stocks do not pretend to be ten independent market sessions.
Minimum20distinct dates plus5distinct dates of each class is a versioned
engineering support gate; it does not prove sufficient statistical power.
Sparse heads remain on expert prior. Full emits forecasts from day one.

Fits use ridge10 around the published starting hypothesis, with a shared
intercept,13values and13missing masks. Every artifact records counts/date counts,
training hash, feature schema, fit time, weights and qualified=false. Feature
schema hash is separate from code version: compatible historical records remain
usable across code releases; incompatible normalizers require a schema change.
Earliest matching archived run/session is selected before learning; revisions
cannot multiply sample count or select a hindsight winner.

This is sequential numerical refitting, not fine-tuning the language model.
Learning does not imply improved accuracy: retain immutable snapshots and
score Brier/log loss/calibration versus matched original baselines, separately
by horizon/threshold/label/coverage. Use date blocks and untouched future periods
before any promotion. Do not automatically deploy a tuned trading policy.

## Worker and archive/export

Opt-in ALPHA_FULL_ENABLED=true, inside run_daily AFTER baseline export only.
Bootstrap never issues Alpha Full or converts old saved CSVs into backfills.
Before first append, real issue must be within36h after latest completed close;
SQL requires actual latest completed session and a fresh issue stamp. Runtime
errors mark a separate partial phase without suppressing original baseline READY.

ALPHA_FULL_EXPORT is separate JSON: full_run_id, session, manifest120, original
JSON SHA256, chunk_count/continuous indices, encoding=gzip+base64, payload_b64.
Concatenate matching chunks, decode, gzip-decompress, verify raw JSON SHA256.
The durable DB record is written before READY. Compression keeps large repeated
feature/provenance records within bounded-log exports. Idempotent retry exports
saved bytes/body, not a reconstructed forecast or later coefficient snapshot.
Existing Drive CSV automation is unchanged and still expects516; the additional
Full archive is in private research SQL and its own export stream.

Backup/restore now includes fifth schema alpha_full_v1 and exact run-body hashes.
Tests use only self-authored fixtures and a disposable loopback PostgreSQL16.2;
no real licensed observations or private CSVs are committed. No real Full issue,
learned live artifact or actual SA consumption is claimed from synthetic tests.

## Validation checkpoint
Native disposable PostgreSQL16.2:29Full+32context+9knowledge=70PASS,0skips.
SQL011 applied, atomic120/idempotency/immutability/fixture/current-session/NULL/
coherence guards tested. Fifth-schema backup/restore has one synthetic run and
exact body hashes. No real forecasts/data/fits. Online knowledge attempted,
URLError; no online PASS. Broad parent DB regression still running at checkpoint.
