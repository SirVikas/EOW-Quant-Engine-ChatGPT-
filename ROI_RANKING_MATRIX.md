# 📊 ROI RANKING MATRIX — GAP-14

**Status:** Decision analysis (no code)
**Engine build:** APP_VERSION 1.95.1
**Answers:** "Across XTE / Lifecycle / Coordinator / Arbiter / Truth / AMIL / RL /
NEXUS / CORTEX — what is the highest-ROI next step, scientifically ranked?"

---

## 1. METHOD

Each candidate scored 1–5 on five axes. **Time-to-evidence** = how fast a
go/no-go verdict is reachable (higher = faster). **Risk** and **Cost** are
inverted (5 = low risk / low cost). Net = weighted toward *evidence value* and
*low risk* at this stage, because the institution's binding constraint is proof,
not capability (per the round-3 reviewer verdict).

`Net = Impact·0.30 + EvidenceValue·0.30 + Risk·0.20 + (6−Cost)·0.10 + TimeToEvidence·0.10`

---

## 2. MATRIX

| Candidate | Impact | Evidence value | Risk (5=safe) | Cost (5=cheap) | Time-to-evidence | **Net** | Rank |
|-----------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **Enable XTE evidence campaign** (obs+path) | 4 | 5 | 5 | 5 | 5 | **4.7** | **1** |
| **Economic proof from campaign** (verdict) | 5 | 5 | 5 | 5 | 4 | **4.8** | **1=** |
| Exit Coordinator X3 (authority) | 5 | 3 | 2 | 3 | 3 | 3.5 | 3 |
| Truth → ADVISE (lifecycle) | 4 | 3 | 2 | 3 | 3 | 3.2 | 4 |
| System Arbiter | 4 | 2 | 2 | 2 | 2 | 2.7 | 6 |
| MarketState Brain (AMIL-A) | 3 | 2 | 3 | 2 | 2 | 2.6 | 7 |
| AMIL Knowledge→Decision | 4 | 2 | 2 | 1 | 1 | 2.5 | 8 |
| NEXUS/CORTEX/OBSX upgrades | 1 | 1 | 4 | 2 | 2 | 1.9 | 9 |
| RL retune (independent) | 3 | 3 | 3 | 3 | 3 | 3.0 | 5 |

*(Campaign + its economic proof are one coupled step; both top the list.)*

---

## 3. SCIENTIFIC CONCLUSION

1. **#1 — Run the XTE evidence campaign and read its economic verdict.** It is the
   cheapest, safest, fastest-to-verdict action and it *gates the value of every
   item below it*. Until it returns CANDIDATE, the expected ROI of X3 / Truth /
   Arbiter / AMIL for XTE is **unknown** — building them first is negative-EV.
2. **#3 — Exit Coordinator X3** is the highest-impact *structural* step and the
   prerequisite for any acting Truth/Arbiter work, but it ranks below the campaign
   because its ROI is conditional on the campaign verdict and it carries real
   (live-exit) risk → must be parity-proven + ADR-gated.
3. **AMIL ranks last-but-one by current ROI** — high eventual impact but highest
   cost, longest time-to-evidence, and fully gated. Correctly deferred.
4. **NEXUS/CORTEX/OBSX upgrades have the lowest trade ROI** (decision-mute by
   design) — keep as support, do not prioritize for trade outcomes.

---

## 4. THIS MATCHES THE REVIEWER

The reviewer's P1–P8 ladder and this scientific ranking agree: **evidence first
(P1–P4), then X3 (P5), then Truth feedback (P6), then Arbiter (P7), then AMIL
(P8).** The one-line takeaway is identical — *the next dollar of effort belongs to
proof, not architecture.*

---

*End of ROI_RANKING_MATRIX. Highest-ROI next step: enable the XTE campaign and
obtain its economic verdict. Everything else is conditional on that result.*
