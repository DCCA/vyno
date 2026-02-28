from __future__ import annotations

from pathlib import Path

import yaml

from digest.config import ProfileConfig, parse_profile_dict, profile_to_dict


def load_effective_profile_dict(base_path: str, overlay_path: str) -> dict:
    base = _read_yaml_dict(base_path)
    overlay = _read_yaml_dict(overlay_path)
    return _deep_merge(base, overlay)


def load_effective_profile(base_path: str, overlay_path: str) -> ProfileConfig:
    merged = load_effective_profile_dict(base_path, overlay_path)
    return parse_profile_dict(merged)


def save_profile_overlay(
    base_path: str,
    overlay_path: str,
    profile_payload: dict,
) -> dict:
    target_profile = parse_profile_dict(profile_payload)
    target = profile_to_dict(target_profile)

    base_raw = _read_yaml_dict(base_path)
    base_profile = parse_profile_dict(base_raw)
    base_canonical = profile_to_dict(base_profile)

    overlay = _dict_diff(base_canonical, target)
    _write_yaml_dict(overlay_path, overlay)
    return overlay


def _read_yaml_dict(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid YAML object at {path}")
    return raw


def _write_yaml_dict(path: str | Path, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(payload or {}, sort_keys=False), encoding="utf-8")
    tmp.replace(p)


def _deep_merge(base: dict, overlay: dict) -> dict:
    merged: dict = {}
    keys = set(base) | set(overlay)
    for key in keys:
        base_value = base.get(key)
        overlay_value = overlay.get(key)
        if isinstance(base_value, dict) and isinstance(overlay_value, dict):
            merged[key] = _deep_merge(base_value, overlay_value)
            continue
        if key in overlay:
            merged[key] = overlay_value
            continue
        merged[key] = base_value
    return merged


def _dict_diff(base: dict, target: dict) -> dict:
    out: dict = {}
    keys = set(base) | set(target)
    for key in keys:
        base_value = base.get(key)
        target_value = target.get(key)
        if isinstance(base_value, dict) and isinstance(target_value, dict):
            nested = _dict_diff(base_value, target_value)
            if nested:
                out[key] = nested
            continue
        if target_value != base_value:
            out[key] = target_value
    return out
