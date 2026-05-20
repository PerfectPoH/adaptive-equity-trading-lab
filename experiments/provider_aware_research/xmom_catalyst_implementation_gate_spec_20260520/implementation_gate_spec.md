# Implementation Gate Spec - TRIAL-XMOM-CATALYST-001

Status:

```text
SPEC_ONLY_NOT_EXECUTABLE
```

## Research Problem

`TRIAL-XMOM-001` showed that catalyst exposure is not an edge. The next research question is narrower:

```text
Can a preregistered catalyst-aware momentum rule distinguish post-catalyst continuation from post-catalyst fade?
```

This spec defines the gate that must exist before any executable rule is created.

Gate id:

```text
IMPL-GATE-XMOM-CATALYST-001
```

## Phase 1 - Feature Discovery

Phase 1 is in-sample only.

Allowed work:

```text
compute pure feature distributions
estimate ECDF percentiles
define candidate threshold-selection policy
run CPCV diagnostics inside the in-sample universe
record trial accounting
estimate effective independent trial count
```

Blocked work:

```text
read OOS PnL
optimize on OOS return
select thresholds from TRIAL-XMOM-001 PnL
select thresholds from CRMD/AEHR winner anatomy
authorize execution
```

Thresholds must be selected blind to returns. For example:

```text
tau_v = ECDF_inverse(V_decay, percentile)
tau_c = ECDF_inverse(C_lag, percentile)
```

The percentile may be preregistered, but the numeric threshold comes only from the in-sample feature distribution.

## Phase 1 Validation

The implementation must use leakage controls before any final pass:

```text
purging: remove train observations whose label windows overlap validation windows
embargoing: remove post-validation buffer observations from train windows
CPCV: generate multiple purged and embargoed validation paths
trial accounting: count all explored variants
effective N: estimate independent trial count from correlated trial return profiles
```

If ONC is not stable, the fallback is conservative hierarchical clustering or nominal trial count.

## Phase 2 - Final Pass

Phase 2 can only happen after a signed manifest freezes:

```text
in_sample_universe
oos_universe
in_sample_window
oos_window
selected_percentiles
resolved_thresholds
purge_window
embargo_window
CPCV configuration
trial_count_nominal
trial_count_effective
sharpe_variance_across_trials
DSR threshold
```

The OOS pass is single-use.

Failure rule:

```text
If the final pass fails, the hypothesis is rejected. Parameter adjustment requires a new preregistration.
```

## DSR Gate

The final pass must compute:

```text
observed Sharpe
sample length T
skewness
kurtosis
expected maximum Sharpe from effective N
PSR
DSR
```

Decision rule:

```text
DSR >= 0.95 is required for any future promotion discussion.
DSR < 0.95 triggers kill_switch_reject.
```

The DSR gate is necessary but not sufficient. Outlier contribution, sample size, liquidity, participation and post-run validation gates still apply.

## Mathematical Form

Blind threshold:

```text
tau_v = CDF^-1(0.80)
```

Expected maximum Sharpe:

```text
E[max_SR] ~= sqrt(V) * ((1 - gamma) * Z^-1(1 - 1/N) + gamma * Z^-1(1 - 1/(N * e)))
```

Probabilistic Sharpe Ratio:

```text
PSR(SR*) = Z(((SR_hat - SR*) * sqrt(T - 1)) / sqrt(1 - skew * SR_hat + ((kurtosis - 1) / 4) * SR_hat^2))
```

Deflated Sharpe Ratio:

```text
DSR = PSR(E[max_SR])
```

## Sources

- DellaVigna and Pollet, "Investor Inattention and Friday Earnings Announcements": https://ideas.repec.org/a/bla/jfinan/v64y2009i2p709-749.html
- DellaVigna and Pollet, "Investor Inattention, Firm Reaction, and Friday Earnings Announcements", NBER Working Paper 11683: https://www.nber.org/papers/w11683
- Sadka, "Momentum and post-earnings-announcement drift anomalies: The role of liquidity risk": https://ideas.repec.org/a/eee/jfinec/v80y2006i2p309-349.html
- Bailey and Lopez de Prado, "The Deflated Sharpe Ratio": https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf
- Lopez de Prado, "Determining Optimal Trading Rules without Backtesting": https://arxiv.org/abs/1408.1159

## Decision

This spec is valid only as an implementation gate design.

It does not make `TRIAL-XMOM-CATALYST-001` executable.
