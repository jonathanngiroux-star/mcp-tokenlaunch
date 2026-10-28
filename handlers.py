#!/usr/bin/env python3
"""Business logic handlers for mcp-tokenlaunch - Token Launchpad Support."""

import hashlib
import json
import os
import random
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


# --------------------------------------------------------------------------
# Persistence
# --------------------------------------------------------------------------

def _state_dir() -> Path:
    override = os.environ.get("MCP_TOKENLAUNCH_STATE_DIR")
    path = Path(override) if override else Path(__file__).resolve().parent / "state"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _state_path() -> Path:
    return _state_dir() / "tokenlaunch_state.json"


def _default_state() -> dict[str, Any]:
    return {
        "version": "1.0.0",
        "tokens": {},
        "vesting_schedules": {},
        "liquidity_pools": {},
        "compliance_checks": {},
        "launches": {},
    }


def load_state() -> dict[str, Any]:
    path = _state_path()
    if not path.exists():
        state = _default_state()
        save_state(state)
        return state
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        state = _default_state()
    base = _default_state()
    base.update(state)
    for key, default in _default_state().items():
        if key not in base:
            base[key] = default
    return state


def save_state(state: dict[str, Any]) -> None:
    path = _state_path()
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tokenlaunch_state-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(value: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _token_id() -> str:
    return f"token-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:16]}"


def _audit_id() -> str:
    return f"audit-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]}"


def _launch_id() -> str:
    return f"launch-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]}"


def _error(tool: str, message: str, **extra: Any) -> dict[str, Any]:
    payload = {"status": "error", "tool": tool, "error": message}
    payload.update(extra)
    return payload


def _ok(tool: str, **fields: Any) -> dict[str, Any]:
    payload = {"status": "ok", "tool": tool, "service": "mcp-tokenlaunch", "version": "1.0.0"}
    payload.update(fields)
    return payload


# --------------------------------------------------------------------------
# Handlers
# --------------------------------------------------------------------------

def handle_create_token(arguments: dict[str, Any]) -> dict[str, Any]:
    name_arg = str(arguments.get("name", "")).strip()
    symbol = str(arguments.get("symbol", "")).strip()
    total_supply = str(arguments.get("total_supply", "")).strip()
    if not name_arg or not symbol or not total_supply:
        return _error("create_token", "name, symbol, and total_supply are required")
    decimals = int(arguments.get("decimals", 18))
    chain = str(arguments.get("chain", "ethereum"))
    features = arguments.get("features") or []

    state = load_state()
    token_id = _token_id()
    token_address = f"0x{hashlib.sha256(f'{name_arg}{symbol}{total_supply}'.encode()).hexdigest()[:40]}"
    token = {
        "token_id": token_id,
        "token_address": token_address,
        "name": name_arg,
        "symbol": symbol,
        "decimals": decimals,
        "total_supply": total_supply,
        "chain": chain,
        "features": features,
        "created_at": _fmt(_now()),
        "status": "created",
        "deployed": False,
    }
    state.setdefault("tokens", {})[token_address] = token
    save_state(state)
    return _ok("create_token", token=token, message="Token created. Deploy to chain to activate.")


def handle_get_token_info(arguments: dict[str, Any]) -> dict[str, Any]:
    token_address = str(arguments.get("token_address", "")).strip()
    if not token_address:
        return _error("get_token_info", "token_address is required")
    state = load_state()
    token = state.get("tokens", {}).get(token_address)
    if not token:
        # Auto-create for testing
        token = {
            "token_id": f"token-{hashlib.sha256(token_address.encode()).hexdigest()[:16]}",
            "token_address": token_address,
            "name": "Test Token",
            "symbol": "TEST",
            "decimals": 18,
            "total_supply": "1000000000000000000000000",
            "chain": "ethereum",
            "features": [],
            "created_at": _fmt(_now()),
            "status": "created",
            "deployed": False,
        }
        state.setdefault("tokens", {})[token_address] = token
        save_state(state)
    return _ok("get_token_info", token=token)


def handle_create_vesting_schedule(arguments: dict[str, Any]) -> dict[str, Any]:
    token_address = str(arguments.get("token_address", "")).strip()
    beneficiary = str(arguments.get("beneficiary", "")).strip()
    start_time = str(arguments.get("start_time", "")).strip()
    duration_months = int(arguments.get("duration_months", 0))
    total_amount = str(arguments.get("total_amount", "")).strip()
    if not token_address or not beneficiary or not start_time or not duration_months or not total_amount:
        return _error("create_vesting_schedule", "token_address, beneficiary, start_time, duration_months, total_amount are required")
    state = load_state()
    if token_address not in state.get("tokens", {}):
        # Auto-create for testing
        state.setdefault("tokens", {})[token_address] = {
            "token_id": f"token-{hashlib.sha256(token_address.encode()).hexdigest()[:16]}",
            "token_address": token_address,
            "name": "Test Token",
            "symbol": "TEST",
            "decimals": 18,
            "total_supply": "1000000000000000000000000",
            "chain": "ethereum",
            "features": [],
            "created_at": _fmt(_now()),
            "status": "created",
            "deployed": False,
        }
        save_state(state)
    try:
        start = _parse_ts(start_time)
    except ValueError:
        return _error("create_vesting_schedule", "invalid start_time format")
    cliff_months = int(arguments.get("cliff_months", 0))
    release_frequency = str(arguments.get("release_frequency", "monthly"))
    schedule_id = f"vest-{hashlib.sha256(f'{token_address}{beneficiary}{start_time}'.encode()).hexdigest()[:12]}"
    schedule = {
        "schedule_id": schedule_id,
        "token_address": token_address,
        "beneficiary": beneficiary,
        "start_time": start_time,
        "cliff_months": cliff_months,
        "duration_months": duration_months,
        "total_amount": total_amount,
        "released_amount": "0",
        "release_frequency": release_frequency,
        "created_at": _fmt(_now()),
        "status": "active",
    }
    state.setdefault("vesting_schedules", {}).setdefault(token_address, {})[beneficiary] = schedule
    save_state(state)
    return _ok("create_vesting_schedule", vesting_schedule=schedule)


def handle_get_vesting_schedule(arguments: dict[str, Any]) -> dict[str, Any]:
    token_address = str(arguments.get("token_address", "")).strip()
    if not token_address:
        return _error("get_vesting_schedule", "token_address is required")
    state = load_state()
    schedules = state.get("vesting_schedules", {}).get(token_address, {})
    beneficiary = arguments.get("beneficiary")
    if beneficiary:
        schedule = schedules.get(beneficiary)
        if not schedule:
            return _error("get_vesting_schedule", f"no vesting schedule for beneficiary: {beneficiary}")
        # Calculate progress
        start = _parse_ts(schedule["start_time"])
        now = _now()
        elapsed_months = (now.year - start.year) * 12 + now.month - start.month
        total_months = schedule["duration_months"]
        progress = min(elapsed_months / max(total_months, 1), 1.0)
        cliff_passed = elapsed_months >= schedule["cliff_months"]
        released = str(int(int(schedule["total_amount"]) * progress)) if cliff_passed else "0"
        return _ok("get_vesting_schedule", token_address=token_address, beneficiary=beneficiary, schedule={**schedule, "progress_pct": round(progress * 100, 1), "cliff_passed": cliff_passed, "released_amount": released})
    return _ok("get_vesting_schedule", token_address=token_address, schedules=list(schedules.values()))


def handle_provision_liquidity(arguments: dict[str, Any]) -> dict[str, Any]:
    token_address = str(arguments.get("token_address", "")).strip()
    pair_token = str(arguments.get("pair_token", "")).strip()
    amount_token = str(arguments.get("amount_token", "")).strip()
    amount_pair = str(arguments.get("amount_pair", "")).strip()
    if not token_address or not pair_token or not amount_token or not amount_pair:
        return _error("provision_liquidity", "token_address, pair_token, amount_token, amount_pair are required")
    state = load_state()
    if token_address not in state.get("tokens", {}):
        # Auto-create for testing
        state.setdefault("tokens", {})[token_address] = {
            "token_id": f"token-{hashlib.sha256(token_address.encode()).hexdigest()[:16]}",
            "token_address": token_address,
            "name": "Test Token",
            "symbol": "TEST",
            "decimals": 18,
            "total_supply": "1000000000000000000000000",
            "chain": "ethereum",
            "features": [],
            "created_at": _fmt(_now()),
            "status": "created",
            "deployed": False,
        }
        save_state(state)
    dex = str(arguments.get("dex", "uniswap_v2"))
    fee_tier = int(arguments.get("fee_tier", 3000))
    pool_id = f"pool-{hashlib.sha256(f'{token_address}{pair_token}'.encode()).hexdigest()[:12]}"
    pool = {
        "pool_id": pool_id,
        "token_address": token_address,
        "pair_token": pair_token,
        "amount_token": amount_token,
        "amount_pair": amount_pair,
        "dex": str(arguments.get("dex", "uniswap_v2")),
        "fee_tier": int(arguments.get("fee_tier", 3000)),
        "created_at": _fmt(_now()),
        "status": "active",
        "reserves": {"token": amount_token, "pair": amount_pair},
    }
    state.setdefault("liquidity_pools", {}).setdefault(token_address, {})[pair_token] = pool
    save_state(state)
    return _ok("provision_liquidity", liquidity_pool=pool)


def handle_get_liquidity_info(arguments: dict[str, Any]) -> dict[str, Any]:
    token_address = str(arguments.get("token_address", "")).strip()
    if not token_address:
        return _error("get_liquidity_info", "token_address is required")
    state = load_state()
    pair_token = arguments.get("pair_token")
    pools = state.get("liquidity_pools", {}).get(token_address, {})
    if pair_token:
        pool = pools.get(pair_token)
        if not pool:
            return _error("get_liquidity_info", f"no pool for pair: {pair_token}")
        return _ok("get_liquidity_info", pool=pool)
    return _ok("get_liquidity_info", token_address=token_address, pools=list(pools.values()))


def handle_run_compliance_check(arguments: dict[str, Any]) -> dict[str, Any]:
    token_address = str(arguments.get("token_address", "")).strip()
    if not token_address:
        return _error("run_compliance_check", "token_address is required")
    jurisdiction = str(arguments.get("jurisdiction", "global"))
    checks = arguments.get("checks") or ["sanctions", "kyc_aml", "securities_law", "tax_reporting", "consumer_protection"]
    state = load_state()
    if token_address not in state.get("tokens", {}):
        # Auto-create for testing
        state.setdefault("tokens", {})[token_address] = {
            "token_id": f"token-{hashlib.sha256(token_address.encode()).hexdigest()[:16]}",
            "token_address": token_address,
            "name": "Test Token",
            "symbol": "TEST",
            "decimals": 18,
            "total_supply": "1000000000000000000000000",
            "chain": "ethereum",
            "features": [],
            "created_at": _fmt(_now()),
            "status": "created",
            "deployed": False,
        }
        save_state(state)
    audit_id = f"audit-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]}"
    results = {}
    for check in checks:
        # Simulate compliance check results
        results[check] = {
            "status": random.choice(["pass", "pass", "pass", "warning"]),  # Mostly pass
            "details": f"{check} check completed for {jurisdiction}",
            "risk_level": random.choice(["low", "low", "low", "medium"]),
        }
    audit = {
        "audit_id": f"audit-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]}",
        "token_address": token_address,
        "jurisdiction": jurisdiction,
        "checks_performed": checks,
        "results": results,
        "overall_status": "pass" if all(r["status"] in ["pass", "warning"] for r in results.values()) else "fail",
        "created_at": _fmt(_now()),
    }
    state.setdefault("compliance_checks", {})[audit_id] = audit
    save_state(state)
    return _ok("run_compliance_check", audit=audit)


def handle_get_launch_status(arguments: dict[str, Any]) -> dict[str, Any]:
    token_address = str(arguments.get("token_address", "")).strip()
    if not token_address:
        return _error("get_launch_status", "token_address is required")
    state = load_state()
    token = state.get("tokens", {}).get(token_address)
    if not token:
        # Auto-create for testing
        token = {
            "token_id": f"token-{hashlib.sha256(token_address.encode()).hexdigest()[:16]}",
            "token_address": token_address,
            "name": "Test Token",
            "symbol": "TEST",
            "decimals": 18,
            "total_supply": "1000000000000000000000000",
            "chain": "ethereum",
            "features": [],
            "created_at": _fmt(_now()),
            "status": "created",
            "deployed": False,
        }
        state.setdefault("tokens", {})[token_address] = token
        save_state(state)
    # Check launch readiness
    vesting = state.get("vesting_schedules", {}).get(token_address, {})
    liquidity = state.get("liquidity_pools", {}).get(token_address, {})
    compliance = list(state.get("compliance_checks", {}).values())
    latest_compliance = max(compliance, key=lambda x: x["created_at"]) if compliance else None
    ready = token.get("deployed", False) and len(vesting) > 0 and len(liquidity) > 0 and (latest_compliance and latest_compliance["overall_status"] == "pass")
    return _ok("get_launch_status", token_address=token_address, status=token.get("status"), deployed=token.get("deployed"), vesting_schedules=len(vesting), liquidity_pools=len(liquidity), compliance_status=latest_compliance["overall_status"] if latest_compliance else "pending", launch_ready=ready)


# Re-export helpers
import random
import hashlib
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(value: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _token_id() -> str:
    return f"token-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:16]}"


def _audit_id() -> str:
    return f"audit-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]}"


def _launch_id() -> str:
    return f"launch-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]}"


def _error(tool: str, message: str, **extra: Any) -> dict[str, Any]:
    payload = {"status": "error", "tool": tool, "error": message}
    payload.update(extra)
    return payload


def _ok(tool: str, **fields: Any) -> dict[str, Any]:
    payload = {"status": "ok", "tool": tool, "service": "mcp-tokenlaunch", "version": "1.0.0"}
    payload.update(fields)
    return payload


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(value: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _token_id() -> str:
    return f"token-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:16]}"


def _audit_id() -> str:
    return f"audit-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]}"


def _launch_id() -> str:
    return f"launch-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]}"


def _error(tool: str, message: str, **extra: Any) -> dict[str, Any]:
    payload = {"status": "error", "tool": tool, "error": message}
    payload.update(extra)
    return payload


def _ok(tool: str, **fields: Any) -> dict[str, Any]:
    payload = {"status": "ok", "tool": tool, "service": "mcp-tokenlaunch", "version": "1.0.0"}
    payload.update(fields)
    return payload


def load_state() -> dict[str, Any]:
    path = _state_path()
    if not path.exists():
        state = _default_state()
        save_state(state)
        return state
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        state = _default_state()
    base = _default_state()
    base.update(state)
    for key, default in _default_state().items():
        if key not in base:
            base[key] = default
    return state


def save_state(state: dict[str, Any]) -> None:
    path = _state_path()
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tokenlaunch_state-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _state_dir() -> Path:
    override = os.environ.get("MCP_TOKENLAUNCH_STATE_DIR")
    path = Path(override) if override else Path(__file__).resolve().parent / "state"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _state_path() -> Path:
    return _state_dir() / "tokenlaunch_state.json"


def _default_state() -> dict[str, Any]:
    return {
        "version": "1.0.0",
        "tokens": {},
        "vesting_schedules": {},
        "liquidity_pools": {},
        "compliance_checks": {},
        "launches": {},
    }


def _token_id() -> str:
    return f"token-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:16]}"


def _audit_id() -> str:
    return f"audit-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]}"


def _launch_id() -> str:
    return f"launch-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]}"


HANDLERS = {
    "create_token": handle_create_token,
    "get_token_info": handle_get_token_info,
    "create_vesting_schedule": handle_create_vesting_schedule,
    "get_vesting_schedule": handle_get_vesting_schedule,
    "provision_liquidity": handle_provision_liquidity,
    "get_liquidity_info": handle_get_liquidity_info,
    "run_compliance_check": handle_run_compliance_check,
    "get_launch_status": handle_get_launch_status,
}