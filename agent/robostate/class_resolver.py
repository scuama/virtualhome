"""Deterministic scene-class normalization shared by RoboState modules."""

from __future__ import annotations

import re
from typing import Iterable, Optional


STATE_MODIFIERS = {
    "broken",
    "clean",
    "closed",
    "cold",
    "dirty",
    "empty",
    "filled",
    "hot",
    "inactive",
    "off",
    "on",
    "open",
    "plugged",
    "powered",
    "sliced",
    "unplugged",
}

GENERIC_SUFFIXES = {
    "book",
    "bowl",
    "computer",
    "controller",
    "cup",
    "device",
    "folder",
    "glass",
    "item",
    "plate",
    "remote",
    "screen",
}


def compact_class_name(value: str) -> str:
    """Normalize separators and quantity suffixes without guessing semantics."""
    text = re.sub(r"_\d+$", "", str(value or "").strip().lower())
    return re.sub(r"[^a-z0-9]", "", text)


def _compact_variants(value: str) -> set[str]:
    compact = compact_class_name(value)
    variants = {compact}
    if compact.endswith("ies") and len(compact) > 3:
        variants.add(compact[:-3] + "y")
    if compact.endswith("sses") and len(compact) > 2:
        variants.add(compact[:-2])
    elif compact.endswith("s") and not compact.endswith("ss"):
        variants.add(compact[:-1])
    return {item for item in variants if item}


def _without_state_modifiers(value: str) -> str:
    parts = [
        part
        for part in re.split(r"[^a-z0-9]+", str(value or "").strip().lower())
        if part and part not in STATE_MODIFIERS
    ]
    return "".join(parts)


def resolve_scene_class(
    value: str,
    scene_classes: Iterable[str],
) -> Optional[str]:
    """Resolve a model-produced class to one unique observed scene class.

    Exact compact equivalence is preferred. Descriptive state modifiers may be
    removed, and a generic suffix such as ``glass`` is accepted only when it
    identifies one unique scene class.
    """
    catalog = sorted({
        str(item).strip().lower()
        for item in scene_classes
        if str(item).strip()
    })
    if not value or str(value).strip().startswith("?"):
        return None

    variants = _compact_variants(value)
    compact = compact_class_name(value)
    exact = [
        item for item in catalog
        if compact_class_name(item) in variants
    ]
    if len(exact) == 1:
        return exact[0]

    stripped = _without_state_modifiers(re.sub(r"_\d+$", "", str(value)))
    if stripped and stripped != compact:
        stripped_variants = _compact_variants(stripped)
        exact = [
            item for item in catalog
            if compact_class_name(item) in stripped_variants
        ]
        if len(exact) == 1:
            return exact[0]

    # Models sometimes shorten a compound VirtualHome class (for example,
    # ``waterglass`` to ``glass``). Resolve only when the scene makes it unique.
    suffix_matches = []
    if variants.intersection(GENERIC_SUFFIXES):
        suffix_matches = [
            item for item in catalog
            if any(
                compact_class_name(item).endswith(candidate)
                for candidate in variants.intersection(GENERIC_SUFFIXES)
            )
        ]
    if len(suffix_matches) == 1:
        return suffix_matches[0]
    return None


def canonicalize_selected_classes(
    selected_classes: Iterable[str],
    scene_classes: Iterable[str],
) -> set[str]:
    """Return only model selections that resolve to observed scene classes."""
    return {
        resolved
        for value in selected_classes
        if (resolved := resolve_scene_class(value, scene_classes)) is not None
    }


def instruction_scene_classes(
    instruction: str,
    scene_classes: Iterable[str],
) -> set[str]:
    """Find scene classes explicitly named by contiguous instruction words."""
    words = re.findall(r"[a-z0-9]+", str(instruction or "").lower())
    resolved = set()
    for start in range(len(words)):
        for width in range(1, min(5, len(words) - start + 1)):
            candidate = " ".join(words[start:start + width])
            match = resolve_scene_class(candidate, scene_classes)
            if match:
                resolved.add(match)
    return resolved
