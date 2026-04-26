"""
Tests for Universal Performance Explorer (FTD).
All tests are self-contained — no external state file required.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from datetime import datetime, timezone

import pytest

from core.performance_explorer import (
    BackupManager,
    ExportEngine,
    PatternInsight,
    PerformanceExplorer,
    SummaryPanel,
    TradeFilter,
    TradeRecord,
    PRESETS,
    build_visual_data,
    compute_summary,
    extract_insights,
    load_trades_from_state,
    preset_filter,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def _make_trade(
    trade_id:    str   = "t1",
    symbol:      str   = "BTCUSDT",
    side:        str   = "LONG",
    strategy_id: str   = "TF_EMA_RSI_v1",
    regime:      str   = "TRENDING",
    net_pnl:     float = 2.0,
    gross_pnl:   float = 2.5,
    fee_entry:   float = 0.1,
    fee_exit:    float = 0.1,
    r_multiple:  float = 1.0,
    exit_ts:     int   = None,
) -> TradeRecord:
    if exit_ts is None:
        exit_ts = int(time.time() * 1000)
    return TradeRecord(
        trade_id      = trade_id,
        symbol        = symbol,
        side          = side,
        strategy_id   = strategy_id,
        regime        = regime,
        order_type    = "LIMIT",
        entry_price   = 100.0,
        exit_price    = 102.0,
        qty           = 1.0,
        gross_pnl     = gross_pnl,
        fee_entry     = fee_entry,
        fee_exit      = fee_exit,
        slippage_cost = 0.0,
        net_pnl       = net_pnl,
        net_pnl_pct   = net_pnl / 100,
        r_multiple    = r_multiple,
        entry_ts      = exit_ts - 60_000,
        exit_ts       = exit_ts,
        mode          = "PAPER",
    )


def _sample_trades() -> list[TradeRecord]:
    now = int(time.time() * 1000)
    return [
        _make_trade("t1", "BTCUSDT", "LONG",  "TF_EMA_RSI_v1", "TRENDING",       net_pnl= 2.0, gross_pnl= 2.5, r_multiple= 1.2),
        _make_trade("t2", "BTCUSDT", "SHORT", "TF_EMA_RSI_v1", "TRENDING",       net_pnl=-3.0, gross_pnl=-2.5, fee_entry=0.15, fee_exit=0.15, r_multiple=-1.5),
        _make_trade("t3", "ETHUSDT", "LONG",  "MR_BB_RSI_v1",  "MEAN_REVERTING", net_pnl= 1.5, gross_pnl= 1.8, r_multiple= 0.8),
        _make_trade("t4", "ETHUSDT", "SHORT", "MR_BB_RSI_v1",  "MEAN_REVERTING", net_pnl=-1.0, gross_pnl=-0.7, r_multiple=-0.5),
        _make_trade("t5", "SOLUSDT", "LONG",  "TF_EMA_RSI_v1", "TRENDING",       net_pnl= 0.5, gross_pnl= 0.8, r_multiple= 0.3),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Part 2: Preset tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPresets:
    def test_all_presets_defined(self):
        for label in ["1D", "3D", "7D", "20D", "60D", "100D", "180D", "365D", "ALL"]:
            assert label in PRESETS

    def test_all_preset_returns_no_date_filter(self):
        flt = preset_filter("ALL")
        assert flt.date_from is None
        assert flt.date_to is None

    def test_1d_preset_cuts_off_old_trades(self):
        old_ts  = int((time.time() - 2 * 86400) * 1000)
        new_ts  = int(time.time() * 1000)
        trades  = [_make_trade("old", exit_ts=old_ts), _make_trade("new", exit_ts=new_ts)]
        flt     = preset_filter("1D")
        result  = flt.apply(trades)
        assert len(result) == 1
        assert result[0].trade_id == "new"

    def test_case_insensitive(self):
        flt = preset_filter("7d")
        assert flt.date_from is not None


# ─────────────────────────────────────────────────────────────────────────────
# Part 3: Filter tests
# ─────────────────────────────────────────────────────────────────────────────

class TestTradeFilter:
    def test_symbol_filter(self):
        trades = _sample_trades()
        flt    = TradeFilter(symbols=["BTCUSDT"])
        result = flt.apply(trades)
        assert all(t.symbol == "BTCUSDT" for t in result)
        assert len(result) == 2

    def test_strategy_filter(self):
        trades = _sample_trades()
        flt    = TradeFilter(strategies=["MR_BB_RSI_v1"])
        result = flt.apply(trades)
        assert all(t.strategy_id == "MR_BB_RSI_v1" for t in result)

    def test_win_only_filter(self):
        trades = _sample_trades()
        flt    = TradeFilter(win_only=True)
        result = flt.apply(trades)
        assert all(t.net_pnl > 0 for t in result)

    def test_loss_only_filter(self):
        trades = _sample_trades()
        flt    = TradeFilter(loss_only=True)
        result = flt.apply(trades)
        assert all(t.net_pnl <= 0 for t in result)

    def test_rr_range_filter(self):
        trades = _sample_trades()
        flt    = TradeFilter(rr_min=0.5, rr_max=1.5)
        result = flt.apply(trades)
        assert all(0.5 <= t.r_multiple <= 1.5 for t in result)

    def test_pnl_range_filter(self):
        trades = _sample_trades()
        flt    = TradeFilter(pnl_min=1.0)
        result = flt.apply(trades)
        assert all(t.net_pnl >= 1.0 for t in result)

    def test_regime_filter(self):
        trades = _sample_trades()
        flt    = TradeFilter(regimes=["MEAN_REVERTING"])
        result = flt.apply(trades)
        assert all(t.regime == "MEAN_REVERTING" for t in result)

    def test_side_filter(self):
        trades = _sample_trades()
        flt    = TradeFilter(sides=["LONG"])
        result = flt.apply(trades)
        assert all(t.side == "LONG" for t in result)

    def test_empty_result_ok(self):
        trades = _sample_trades()
        flt    = TradeFilter(symbols=["NONEXISTENT"])
        assert flt.apply(trades) == []


# ─────────────────────────────────────────────────────────────────────────────
# Part 4: Summary panel tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSummaryPanel:
    def test_empty_trades(self):
        s = compute_summary([])
        assert s.total_trades == 0
        assert s.net_pnl == 0.0

    def test_basic_metrics(self):
        trades = _sample_trades()
        s      = compute_summary(trades, initial_capital=1000.0)
        assert s.total_trades == 5
        assert s.wins  == 3
        assert s.losses == 2
        assert abs(s.net_pnl - (2.0 - 3.0 + 1.5 - 1.0 + 0.5)) < 0.01

    def test_win_rate(self):
        trades = _sample_trades()
        s      = compute_summary(trades)
        assert abs(s.win_rate - 60.0) < 0.1

    def test_profit_factor_positive(self):
        wins = [_make_trade(f"w{i}", net_pnl=2.0, gross_pnl=2.0) for i in range(3)]
        s    = compute_summary(wins)
        assert s.profit_factor == 99.99

    def test_strategy_breakdown_populated(self):
        trades = _sample_trades()
        s      = compute_summary(trades)
        assert "TF_EMA_RSI_v1" in s.by_strategy
        assert "MR_BB_RSI_v1"  in s.by_strategy

    def test_regime_breakdown_populated(self):
        trades = _sample_trades()
        s      = compute_summary(trades)
        assert "TRENDING" in s.by_regime
        assert "MEAN_REVERTING" in s.by_regime

    def test_symbol_breakdown_sorted_asc(self):
        trades = _sample_trades()
        s      = compute_summary(trades)
        vals   = list(s.by_symbol.values())
        assert vals == sorted(vals)

    def test_max_drawdown_positive(self):
        losing_trades = [
            _make_trade(f"l{i}", net_pnl=-5.0, gross_pnl=-4.0) for i in range(5)
        ]
        s = compute_summary(losing_trades, initial_capital=1000.0)
        assert s.max_drawdown > 0

    def test_cost_pct_calculated(self):
        t = _make_trade(net_pnl=1.5, gross_pnl=2.0, fee_entry=0.2, fee_exit=0.2)
        s = compute_summary([t])
        assert s.cost_pct > 0


# ─────────────────────────────────────────────────────────────────────────────
# Part 5: Visual data tests
# ─────────────────────────────────────────────────────────────────────────────

class TestVisualData:
    def test_empty_trades(self):
        v = build_visual_data([])
        assert v.equity_curve == []
        assert v.drawdown_series == []

    def test_equity_curve_length(self):
        trades = _sample_trades()
        v      = build_visual_data(trades)
        assert len(v.equity_curve) == len(trades)

    def test_drawdown_non_negative(self):
        trades = _sample_trades()
        v      = build_visual_data(trades)
        assert all(p["drawdown_pct"] >= 0 for p in v.drawdown_series)

    def test_win_loss_dist_sums_to_total(self):
        trades = _sample_trades()
        v      = build_visual_data(trades)
        total  = v.win_loss_dist["wins"] + v.win_loss_dist["losses"] + v.win_loss_dist["breakeven"]
        assert total == len(trades)

    def test_histogram_buckets_sum_to_total(self):
        trades = _sample_trades()
        v      = build_visual_data(trades)
        assert sum(b["count"] for b in v.pnl_histogram) == len(trades)


# ─────────────────────────────────────────────────────────────────────────────
# Part 6: Export engine tests
# ─────────────────────────────────────────────────────────────────────────────

class TestExportEngine:
    def _summary(self) -> SummaryPanel:
        return compute_summary(_sample_trades())

    def test_csv_has_header(self):
        csv = ExportEngine.to_csv(_sample_trades())
        assert "symbol" in csv.splitlines()[0]

    def test_csv_row_count(self):
        trades = _sample_trades()
        csv    = ExportEngine.to_csv(trades)
        lines  = [l for l in csv.splitlines() if l.strip()]
        assert len(lines) == len(trades) + 1   # header + rows

    def test_json_valid(self):
        data = json.loads(ExportEngine.to_json(_sample_trades(), self._summary()))
        assert "trades" in data
        assert "summary" in data
        assert "exported_at" in data

    def test_markdown_has_summary_table(self):
        md = ExportEngine.to_markdown(_sample_trades(), self._summary(), preset="7D")
        assert "## Summary Panel" in md
        assert "Profit Factor" in md

    def test_markdown_has_strategy_breakdown(self):
        md = ExportEngine.to_markdown(_sample_trades(), self._summary())
        assert "## Strategy Breakdown" in md

    def test_save_writes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.csv")
            ExportEngine.save("hello,world", path)
            assert os.path.exists(path)
            with open(path) as f:
                assert f.read() == "hello,world"


# ─────────────────────────────────────────────────────────────────────────────
# Part 7: Import engine tests
# ─────────────────────────────────────────────────────────────────────────────

class TestImport:
    def _state_file(self, tmp: str, trades: list) -> str:
        path = os.path.join(tmp, "eow_state_test.json")
        with open(path, "w") as f:
            json.dump({"trade_history": trades, "meta": {}}, f)
        return path

    def test_load_from_state_file(self):
        raw = [
            {
                "trade_id": "x1", "symbol": "BTCUSDT", "side": "LONG",
                "strategy_id": "TF_EMA_RSI_v1", "regime": "TRENDING",
                "order_type": "LIMIT", "entry_price": 100.0, "exit_price": 102.0,
                "qty": 1.0, "gross_pnl": 2.0, "fee_entry": 0.1, "fee_exit": 0.1,
                "slippage_cost": 0.0, "net_pnl": 1.8, "net_pnl_pct": 0.018,
                "r_multiple": 1.0, "entry_ts": 1000000, "exit_ts": 2000000, "mode": "PAPER",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path   = self._state_file(tmp, raw)
            trades = load_trades_from_state(path)
            assert len(trades) == 1
            assert trades[0].symbol == "BTCUSDT"

    def test_malformed_trade_skipped(self):
        raw = [
            {"trade_id": "bad", "symbol": None},   # missing required fields
            {
                "trade_id": "ok", "symbol": "BTCUSDT", "side": "LONG",
                "strategy_id": "TF_EMA_RSI_v1", "regime": "TRENDING",
                "order_type": "LIMIT", "entry_price": 100.0, "exit_price": 102.0,
                "qty": 1.0, "gross_pnl": 2.0, "fee_entry": 0.1, "fee_exit": 0.1,
                "slippage_cost": 0.0, "net_pnl": 1.8, "net_pnl_pct": 0.018,
                "r_multiple": 1.0, "entry_ts": 1000000, "exit_ts": 2000000, "mode": "PAPER",
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path   = self._state_file(tmp, raw)
            trades = load_trades_from_state(path)
            assert len(trades) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Part 8: Backup / Restore tests
# ─────────────────────────────────────────────────────────────────────────────

class TestBackupManager:
    def test_backup_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            bm   = BackupManager(tmp)
            path = bm.backup(_sample_trades(), label="test")
            assert os.path.exists(path)

    def test_restore_returns_same_count(self):
        trades = _sample_trades()
        with tempfile.TemporaryDirectory() as tmp:
            bm     = BackupManager(tmp)
            path   = bm.backup(trades, label="test")
            result = bm.restore(path)
            assert len(result) == len(trades)

    def test_list_backups(self):
        with tempfile.TemporaryDirectory() as tmp:
            bm = BackupManager(tmp)
            bm.backup(_sample_trades(), label="a")
            bm.backup(_sample_trades(), label="b")
            assert len(bm.list_backups()) == 2

    def test_latest_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            bm = BackupManager(tmp)
            bm.backup(_sample_trades(), label="first")
            time.sleep(0.01)
            bm.backup(_sample_trades(), label="second")
            latest = bm.latest_backup()
            assert "second" in latest

    def test_auto_backup_once_per_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            bm = BackupManager(tmp)
            bm.auto_backup_if_needed(_sample_trades())
            bm.auto_backup_if_needed(_sample_trades())
            auto_backups = [b for b in bm.list_backups() if "_auto" in b]
            assert len(auto_backups) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Part 9: AI Pattern Engine tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPatternInsights:
    def test_low_pf_triggers_critical(self):
        losing = [
            _make_trade(f"l{i}", net_pnl=-2.0, gross_pnl=-1.5) for i in range(10)
        ]
        s        = compute_summary(losing)
        insights = extract_insights(s, losing)
        crits    = [i for i in insights if i.severity == "CRITICAL" and "expectancy" in i.description]
        assert len(crits) >= 1

    def test_high_fee_drag_triggers_critical(self):
        high_fee_trades = [
            _make_trade(f"f{i}", net_pnl=0.1, gross_pnl=2.0, fee_entry=0.8, fee_exit=0.9)
            for i in range(5)
        ]
        s        = compute_summary(high_fee_trades)
        insights = extract_insights(s, high_fee_trades)
        cost_ins = [i for i in insights if i.pattern_type == "cost_pattern"]
        assert len(cost_ins) >= 1

    def test_losing_strategy_flagged(self):
        bad_trades = [
            _make_trade(f"b{i}", strategy_id="BAD_STRAT", net_pnl=-5.0, gross_pnl=-4.0)
            for i in range(6)
        ]
        s        = compute_summary(bad_trades)
        insights = extract_insights(s, bad_trades)
        strat_ins = [i for i in insights if "BAD_STRAT" in i.description]
        assert len(strat_ins) >= 1

    def test_winning_strategy_flagged(self):
        good_trades = [
            _make_trade(f"g{i}", strategy_id="GOOD_STRAT", net_pnl=2.0, gross_pnl=2.5)
            for i in range(5)
        ]
        s        = compute_summary(good_trades)
        insights = extract_insights(s, good_trades)
        wins_ins = [i for i in insights if i.pattern_type == "winning_pattern"]
        assert len(wins_ins) >= 1

    def test_toxic_symbols_flagged(self):
        toxic = [
            _make_trade(f"t{i}", symbol="TOXICUSDT", net_pnl=-10.0, gross_pnl=-9.0)
            for i in range(3)
        ]
        s        = compute_summary(toxic)
        insights = extract_insights(s, toxic)
        sym_ins  = [i for i in insights if "TOXICUSDT" in str(i.evidence)]
        assert len(sym_ins) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# Main class integration tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPerformanceExplorer:
    def _upe(self) -> PerformanceExplorer:
        with tempfile.TemporaryDirectory() as tmp:
            upe = PerformanceExplorer(_sample_trades(), initial_capital=1000.0)
            upe.BACKUP_DIR = tmp
            upe._backup    = BackupManager(tmp)
            return upe

    def test_explore_all_returns_dict(self):
        upe    = PerformanceExplorer(_sample_trades())
        report = upe.explore(preset="ALL")
        assert "summary" in report
        assert "visuals" in report
        assert "insights" in report
        assert "trades" in report

    def test_explore_preset_filters_correctly(self):
        old_ts  = int((time.time() - 10 * 86400) * 1000)
        new_ts  = int(time.time() * 1000)
        trades  = [
            _make_trade("old", exit_ts=old_ts, net_pnl=5.0),
            _make_trade("new", exit_ts=new_ts, net_pnl=1.0),
        ]
        upe    = PerformanceExplorer(trades)
        report = upe.explore(preset="3D")
        assert report["trade_count"] == 1

    def test_explore_all_presets(self):
        upe     = PerformanceExplorer(_sample_trades())
        results = upe.explore_all_presets()
        assert set(results.keys()) == set(PRESETS.keys())

    def test_get_trade_table(self):
        upe   = PerformanceExplorer(_sample_trades())
        table = upe.get_trade_table(preset="ALL")
        assert len(table) == 5
        assert all("symbol" in row for row in table)

    def test_get_insights(self):
        upe      = PerformanceExplorer(_sample_trades())
        insights = upe.get_insights()
        assert isinstance(insights, list)

    def test_save_report_md(self):
        upe    = PerformanceExplorer(_sample_trades())
        report = upe.explore(preset="ALL")
        with tempfile.TemporaryDirectory() as tmp:
            saved = upe.save_report(report, output_dir=tmp, formats=["md"])
            assert "md" in saved
            assert os.path.exists(saved["md"])

    def test_save_report_json(self):
        upe    = PerformanceExplorer(_sample_trades())
        report = upe.explore()
        with tempfile.TemporaryDirectory() as tmp:
            saved = upe.save_report(report, output_dir=tmp, formats=["json"])
            assert "json" in saved
            with open(saved["json"]) as f:
                data = json.load(f)
            assert "trades" in data

    def test_save_report_csv(self):
        upe    = PerformanceExplorer(_sample_trades())
        report = upe.explore()
        with tempfile.TemporaryDirectory() as tmp:
            saved = upe.save_report(report, output_dir=tmp, formats=["csv"])
            assert "csv" in saved
            with open(saved["csv"]) as f:
                lines = f.readlines()
            assert len(lines) == 6  # header + 5 trades

    def test_custom_filter(self):
        upe    = PerformanceExplorer(_sample_trades())
        flt    = TradeFilter(symbols=["ETHUSDT"])
        report = upe.explore(custom_filter=flt)
        assert all(t["symbol"] == "ETHUSDT" for t in report["trades"])

    def test_from_state_file(self):
        raw = {
            "trade_history": [
                {
                    "trade_id": "s1", "symbol": "BTCUSDT", "side": "LONG",
                    "strategy_id": "TF_EMA_RSI_v1", "regime": "TRENDING",
                    "order_type": "LIMIT", "entry_price": 100.0, "exit_price": 102.0,
                    "qty": 1.0, "gross_pnl": 2.0, "fee_entry": 0.1, "fee_exit": 0.1,
                    "slippage_cost": 0.0, "net_pnl": 1.8, "net_pnl_pct": 0.018,
                    "r_multiple": 1.0, "entry_ts": 1000000, "exit_ts": 2000000, "mode": "PAPER",
                }
            ],
            "meta": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            state_path = os.path.join(tmp, "eow_state_test.json")
            with open(state_path, "w") as f:
                json.dump(raw, f)
            upe    = PerformanceExplorer.from_state_file(state_path)
            report = upe.explore()
            assert report["trade_count"] == 1

    def test_manual_backup_and_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            upe           = PerformanceExplorer(_sample_trades())
            upe.BACKUP_DIR = tmp
            upe._backup    = BackupManager(tmp)
            bkp_path = upe.manual_backup()
            assert os.path.exists(bkp_path)
            upe.restore_from_backup(bkp_path)
            report = upe.explore()
            assert report["trade_count"] == 5
