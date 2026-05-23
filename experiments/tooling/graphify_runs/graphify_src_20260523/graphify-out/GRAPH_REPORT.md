# Graph Report - C:\Users\barak\Documents\Codici Scuola\adaptive-equity-trading-lab\src  (2026-05-23)

## Corpus Check
- 138 files · ~83,658 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1484 nodes · 3498 edges · 65 communities detected
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 587 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]

## God Nodes (most connected - your core abstractions)
1. `run_milestone_1()` - 35 edges
2. `run_small_cap_portfolio_backtest()` - 27 edges
3. `run_walk_forward_validation()` - 26 edges
4. `run_small_cap_historical_report()` - 23 edges
5. `validate_sec8k_tape_oracle_intraday_data_contract()` - 17 edges
6. `validate_xmom_catalyst_implementation_gate()` - 17 edges
7. `validate_xmom_earnings_single_probe_approval()` - 17 edges
8. `validate_xmom_catalyst_preregistration()` - 16 edges
9. `validate_preregistered_research_plan()` - 15 edges
10. `validate_trial_accounting_preregistration()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `XMOMExecutionConfig` --uses--> `SquareRootImpactConfig`  [INFERRED]
  C:\Users\barak\Documents\Codici Scuola\adaptive-equity-trading-lab\src\experiments\xmom_trial_runner.py → C:\Users\barak\Documents\Codici Scuola\adaptive-equity-trading-lab\src\execution\market_impact.py
- `run_milestone_1()` --calls--> `download_universe()`  [INFERRED]
  C:\Users\barak\Documents\Codici Scuola\adaptive-equity-trading-lab\src\pipeline.py → C:\Users\barak\Documents\Codici Scuola\adaptive-equity-trading-lab\src\data\downloader.py
- `run_milestone_1()` --calls--> `load_or_download_market_news()`  [INFERRED]
  C:\Users\barak\Documents\Codici Scuola\adaptive-equity-trading-lab\src\pipeline.py → C:\Users\barak\Documents\Codici Scuola\adaptive-equity-trading-lab\src\news\gdelt_doc.py
- `run_milestone_1()` --calls--> `build_features()`  [INFERRED]
  C:\Users\barak\Documents\Codici Scuola\adaptive-equity-trading-lab\src\pipeline.py → C:\Users\barak\Documents\Codici Scuola\adaptive-equity-trading-lab\src\features\feature_pipeline.py
- `run_milestone_1()` --calls--> `equity_curve_to_frame()`  [INFERRED]
  C:\Users\barak\Documents\Codici Scuola\adaptive-equity-trading-lab\src\pipeline.py → C:\Users\barak\Documents\Codici Scuola\adaptive-equity-trading-lab\src\backtest\metrics.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.03
Nodes (105): run_benchmark_objective_comparison(), build_calibration_report(), _calibration_for_period(), _empty_calibration(), _safe_float(), summarize_calibration(), fit_probability_calibrator(), ProbabilityCalibrator (+97 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (80): _add_check(), _build_parser(), main(), _read_csv(), _read_json(), _read_text_file(), _report(), validate_adjustment_tradability_policy() (+72 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (63): _blocked_execution_payload(), _check(), controlled_backtest_from_frame(), _ensure_dirs(), _execute_databento_probe(), _filter_regular_trading_hours(), _format_markdown_report(), GapRevParameters (+55 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (42): Approximate market impact in bps for daily bars.      impact_bps = coefficient, square_root_impact_bps(), SquareRootImpactConfig, calculate_position_size(), add_small_cap_execution_columns(), _execution_volatility(), _max_liquidity_notional(), _next_open_gap_pct() (+34 more)

### Community 4 - "Community 4"
Cohesion: 0.1
Nodes (45): assert_no_label_overlap(), combinatorial_purged_cv_splits(), _contiguous_time_blocks(), CPCVConfig, CPCVSplit, _embargoed_positions(), expected_cpcv_split_count(), _group_positions_by_time() (+37 more)

### Community 5 - "Community 5"
Cohesion: 0.1
Nodes (46): _add_check(), main(), _read_csv(), _read_text(), _report(), _validate_blocked_actions(), _validate_data_requirements(), _validate_decision() (+38 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (41): build_run_analysis(), build_signal_diagnostics(), _diagnose(), _diagnose_signal_bottleneck(), _mean_on_mask(), _rows_by_symbol(), _safe_number(), _series_mode() (+33 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (42): build_run_manifest(), compute_config_hash(), _detect_git_commit(), _detect_host(), manifest_to_dict(), _normalise_timestamp(), Run manifest small-cap.  Genera un manifest deterministico per ogni run del runn, Costruisce un :class:`RunManifest` deterministico.      Tutti i campi context-de (+34 more)

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (40): _add_check(), _build_parser(), main(), _read_csv(), _read_json(), _read_text(), _report(), _validate_blocked_actions() (+32 more)

### Community 9 - "Community 9"
Cohesion: 0.1
Nodes (32): add_market_regime_guardrail_columns(), _block_reason(), MarketRegimeGuardrailConfig, _required_columns(), _append_reason(), _as_of_label(), _base_row(), build_small_cap_candidate_export() (+24 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (37): build_blocked_actions(), build_dollar_bars(), _check(), _collapse_bucket(), diagnose_bars_file(), diagnostic_verdict(), distribution_stats(), _format_report() (+29 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (32): _add_check(), _build_parser(), _config_hash_match(), _databento_data_exists(), _evaluate_runtime_checks(), _ledger_status_is_prepared(), main(), _read_csv() (+24 more)

### Community 12 - "Community 12"
Cohesion: 0.14
Nodes (23): _build_parser(), _download_symbol_frames(), _load_metadata(), main(), _parse_symbols(), _resolve_trial_accounting(), run_small_cap_historical_experiment(), run_small_cap_watchlist_experiment() (+15 more)

### Community 13 - "Community 13"
Cohesion: 0.15
Nodes (25): build_blocked_actions(), build_multisymbol_timing_panel(), _check(), _event_error(), _event_fieldnames(), _extract_recent_earnings_8k_records(), _fetch_json(), fetch_sec_8k_item_202_events() (+17 more)

### Community 14 - "Community 14"
Cohesion: 0.19
Nodes (21): _check_p1_artifacts(), _check_p2_manifest(), _check_p3_risk_fraction(), _check_p4_cash_ledger(), _check_p5_bootstrap(), _check_p6_random_entry(), _check_p7_ex_topn(), _check_p8_benchmarks() (+13 more)

### Community 15 - "Community 15"
Cohesion: 0.18
Nodes (22): _benchmark_return(), build_small_cap_backtest_report(), _candidate_date_count(), _candidate_summary(), _counts(), _decision(), _dict_lines(), _excess_return() (+14 more)

### Community 16 - "Community 16"
Cohesion: 0.16
Nodes (21): _classification(), classify_earnings_timestamp(), EarningsTimestampClassification, _looks_date_only(), _parse_timestamp(), Map an earnings timestamp to BMO/AMC/DMT/UNSPECIFIED.      This function is inte, _raw_value(), _check() (+13 more)

### Community 17 - "Community 17"
Cohesion: 0.15
Nodes (19): build_features(), atr(), close_position_in_rolling_range(), distance_from_rolling_high(), ema(), macd(), relative_volume(), rolling_volatility() (+11 more)

### Community 18 - "Community 18"
Cohesion: 0.24
Nodes (19): _add_check(), main(), _read_csv(), _read_json(), _read_markdown(), _validate_candidates(), _validate_checklist(), _validate_manifest() (+11 more)

### Community 19 - "Community 19"
Cohesion: 0.21
Nodes (18): _best_symbols(), build_backtest_report(), _decision(), _finding_lines(), _format_pct(), _json_safe(), _read_csv(), _read_json() (+10 more)

### Community 20 - "Community 20"
Cohesion: 0.22
Nodes (19): _benchmark_window(), build_bootstrap_random_baseline_report(), build_small_cap_benchmark_report(), _candidate_dates(), _candidate_holding_return(), _close_return(), _equal_weight_universe_return(), _holding_end_index() (+11 more)

### Community 21 - "Community 21"
Cohesion: 0.23
Nodes (19): _check(), _ensure_dirs(), evaluate_microrev_file(), main(), MicroRevParams, _pstdev(), _read_csv(), _report() (+11 more)

### Community 22 - "Community 22"
Cohesion: 0.23
Nodes (18): _append_execution_ledger(), _append_mini_panel_execution_ledger(), build_dry_run_plan(), _build_parser(), build_real_run_block_report(), _error_report(), _git_sha(), _interpretation_report() (+10 more)

### Community 23 - "Community 23"
Cohesion: 0.21
Nodes (19): _blocked_decision(), build_approval(), _check(), fetch_case_bars(), _fetch_databento_frame(), main(), normalize_bars(), _query_result() (+11 more)

### Community 24 - "Community 24"
Cohesion: 0.2
Nodes (19): build_blocked_actions(), build_event_index(), build_overlap_panel(), build_symbol_calendars(), _check(), _empty_overlap(), main(), _median_pnl() (+11 more)

### Community 25 - "Community 25"
Cohesion: 0.22
Nodes (18): build_blocked_actions(), _check(), _contribution_pct(), diagnose_trade_log(), _format_report(), _has_number(), main(), _read_csv() (+10 more)

### Community 26 - "Community 26"
Cohesion: 0.29
Nodes (17): _add_check(), _build_parser(), main(), _read_csv(), _read_json(), _read_text(), _report(), _validate_blocked_actions() (+9 more)

### Community 27 - "Community 27"
Cohesion: 0.21
Nodes (16): Enum, assert_order_allowed(), _aware_utc(), check_symbol_cooldown(), classify_trade(), CooldownDecision, CoolDownException, governed_metrics() (+8 more)

### Community 28 - "Community 28"
Cohesion: 0.24
Nodes (16): assign_liquidity_buckets(), build_blocked_actions(), _check(), diagnose_trade_liquidity(), _loser_rate(), main(), _median_pnl(), _read_csv() (+8 more)

### Community 29 - "Community 29"
Cohesion: 0.29
Nodes (16): _add_check(), _build_parser(), _execution_config(), main(), _read_csv(), _read_json(), _report(), _safe_float() (+8 more)

### Community 30 - "Community 30"
Cohesion: 0.31
Nodes (16): _add_check(), _build_parser(), main(), _read_csv(), _read_text(), _report(), _validate_blocked_actions(), _validate_decision() (+8 more)

### Community 31 - "Community 31"
Cohesion: 0.25
Nodes (15): build_alpha_candidates(), build_blocked_actions(), _candidate(), _check(), _format_report(), main(), rank_candidates(), _read_csv() (+7 more)

### Community 32 - "Community 32"
Cohesion: 0.26
Nodes (15): build_acceptance_criteria(), build_blocked_actions(), build_one_call_probe_spec(), build_provider_questions(), _check(), _format_report(), main(), _read_csv() (+7 more)

### Community 33 - "Community 33"
Cohesion: 0.25
Nodes (15): build_blocked_actions(), build_event_timing_panel(), _check(), _has_both_classes(), main(), _median_value(), _read_csv(), _report() (+7 more)

### Community 34 - "Community 34"
Cohesion: 0.33
Nodes (15): _add_check(), _build_parser(), main(), _read_csv(), _read_json(), _read_text_file(), _report(), _validate_budget() (+7 more)

### Community 35 - "Community 35"
Cohesion: 0.34
Nodes (14): _add_check(), _build_parser(), main(), _read_csv(), _read_json(), _read_text_file(), _report(), _run_component_validators() (+6 more)

### Community 36 - "Community 36"
Cohesion: 0.34
Nodes (14): _add_check(), _build_parser(), main(), _read_csv(), _read_json(), _read_text_file(), _report(), _validate_blocked_actions() (+6 more)

### Community 37 - "Community 37"
Cohesion: 0.34
Nodes (14): _add_check(), _build_parser(), main(), _read_csv(), _read_json(), _read_text_file(), _report(), _validate_blockers() (+6 more)

### Community 38 - "Community 38"
Cohesion: 0.34
Nodes (14): _add_check(), _build_parser(), main(), _read_csv(), _read_json(), _read_text(), _report(), _validate_blocked() (+6 more)

### Community 39 - "Community 39"
Cohesion: 0.34
Nodes (14): _add_check(), _build_parser(), main(), _read_csv(), _read_json(), _read_text_file(), _report(), _validate_decisions() (+6 more)

### Community 40 - "Community 40"
Cohesion: 0.29
Nodes (14): build_sue_provider_candidates(), _check(), _format_report(), _has_key(), inspect_sue_credentials(), main(), _read_csv(), _report() (+6 more)

### Community 41 - "Community 41"
Cohesion: 0.33
Nodes (14): _add_check(), _build_parser(), _load_validator(), main(), _read_csv(), _read_json(), _read_text_file(), _report() (+6 more)

### Community 42 - "Community 42"
Cohesion: 0.34
Nodes (14): _add_check(), _build_parser(), main(), _read_csv(), _read_json(), _read_text(), _report(), _validate_blocked_actions() (+6 more)

### Community 43 - "Community 43"
Cohesion: 0.34
Nodes (14): _add_check(), _classification_action(), main(), _read_csv(), _read_json(), _read_text(), _report(), _validate_blocked() (+6 more)

### Community 44 - "Community 44"
Cohesion: 0.29
Nodes (13): _all_false(), _check(), create_dollarbar_transform_preregistration(), _input_panel_rows(), main(), _manifest(), _readme(), _report() (+5 more)

### Community 45 - "Community 45"
Cohesion: 0.36
Nodes (13): _add_check(), _build_parser(), main(), _read_csv(), _read_text(), _report(), _validate_blocked_actions(), _validate_data_requirements() (+5 more)

### Community 46 - "Community 46"
Cohesion: 0.23
Nodes (12): build_graphify_dry_run_plan(), main(), _missing(), _normalize_scope(), Validation and dry-run planning for the Graphify local tooling gate., Build a non-executing Graphify command plan after validating the gate., Structured result for Graphify integration artifact checks., Validate the Graphify integration gate artifact. (+4 more)

### Community 47 - "Community 47"
Cohesion: 0.31
Nodes (13): _ensure_dirs(), evaluate_opening_reclaim_event(), _format_report(), main(), OpeningReclaimParams, run_opening_reclaim_probe(), _safe_ratio(), summarize_opening_reclaim_results() (+5 more)

### Community 48 - "Community 48"
Cohesion: 0.29
Nodes (13): build_sec_earnings_event_panel(), _check(), _format_report(), main(), _next_weekday(), _reaction_session_date(), _report(), run_pead_sec_event_source_gate() (+5 more)

### Community 49 - "Community 49"
Cohesion: 0.35
Nodes (13): _add_check(), build_synthetic_labeled_panel(), _last_kept_equals_raw_minus_horizon(), main(), PurgedTemporalSplitConfig, _row_keys(), _validate_embargo(), _validate_input_is_synthetic() (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.29
Nodes (11): DataValidationResult, download_ticker(), download_universe(), _flatten_yfinance_columns(), load_latest_snapshot(), normalize_ohlcv(), validate_ohlcv(), latest_snapshot() (+3 more)

### Community 51 - "Community 51"
Cohesion: 0.33
Nodes (12): _check(), _format_report(), main(), _report(), run_pead_earnings_only_gate(), validate_pead_earnings_only_gate(), _write_csv(), _write_final_decision() (+4 more)

### Community 52 - "Community 52"
Cohesion: 0.4
Nodes (12): _add_check(), main(), _read_csv(), _read_json(), _read_text(), _report(), _validate_blocked(), _validate_checklist() (+4 more)

### Community 53 - "Community 53"
Cohesion: 0.44
Nodes (11): _add_check(), main(), _read_csv(), _read_json(), _read_markdown(), _validate_blockers(), _validate_command(), validate_final_command_review() (+3 more)

### Community 54 - "Community 54"
Cohesion: 0.33
Nodes (11): _add_rolling_news_features(), _covers_range(), _daily_features(), download_market_news(), _fetch_json(), fetch_timeline(), _gdelt_datetime(), load_or_download_market_news() (+3 more)

### Community 55 - "Community 55"
Cohesion: 0.47
Nodes (10): _add_check(), main(), _read_csv(), _read_json(), _read_markdown(), _validate_blockers(), _validate_ledger_gate(), _validate_manifest() (+2 more)

### Community 56 - "Community 56"
Cohesion: 0.44
Nodes (10): _add_check(), _build_parser(), main(), _read_csv(), _read_json(), _read_text_file(), _report(), _validate_event_audit_table() (+2 more)

### Community 57 - "Community 57"
Cohesion: 0.5
Nodes (8): _add_check(), _build_parser(), main(), _read_csv(), _read_json(), _read_text_file(), _report(), validate_run_artifacts()

### Community 58 - "Community 58"
Cohesion: 0.25
Nodes (1): News data connectors.

### Community 59 - "Community 59"
Cohesion: 0.5
Nodes (7): _compare(), _delta(), _flat_row(), _load_run(), _pairwise_compare(), run_calibration_comparison(), _verdict()

### Community 60 - "Community 60"
Cohesion: 0.57
Nodes (6): _compare(), _delta(), _flat_row(), _load_run_summary(), run_news_ablation(), _verdict()

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (0): 

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (0): 

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (0): 

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **15 isolated node(s):** `SmallCapBootstrapRandomBaselineConfig`, `Compute P&L and portfolio return after stripping the top N winners.      The che`, `Approximate market impact in bps for daily bars.      impact_bps = coefficient`, `Raised when a trade-governance input is structurally invalid.`, `Raised when a new order is attempted during a ticker cooldown window.` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 61`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_milestone_1()` connect `Community 0` to `Community 1`, `Community 2`, `Community 6`, `Community 17`, `Community 50`, `Community 54`, `Community 59`, `Community 60`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._
- **Why does `run_walk_forward_validation()` connect `Community 0` to `Community 1`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `run_small_cap_portfolio_backtest()` connect `Community 3` to `Community 1`, `Community 4`, `Community 7`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Are the 328 inferred relationships involving `str` (e.g. with `run_milestone_1()` and `main()`) actually correct?**
  _`str` has 328 INFERRED edges - model-reasoned connections that need verification._
- **Are the 53 inferred relationships involving `ValueError` (e.g. with `build_small_cap_benchmark_report()` and `build_bootstrap_random_baseline_report()`) actually correct?**
  _`ValueError` has 53 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `run_milestone_1()` (e.g. with `download_universe()` and `RuntimeError`) actually correct?**
  _`run_milestone_1()` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `run_small_cap_portfolio_backtest()` (e.g. with `ValueError` and `SmallCapExecutionPlanner`) actually correct?**
  _`run_small_cap_portfolio_backtest()` has 6 INFERRED edges - model-reasoned connections that need verification._