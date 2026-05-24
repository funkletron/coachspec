from __future__ import annotations

from coachspec.modules import default_registry


def test_registry_loads_known_modules() -> None:
    assert default_registry.get("socratic_questioning") is not None
    assert default_registry.get("reflective_listening") is not None
    assert default_registry.get("deliberate_practice") is not None


def test_module_ids_are_unique() -> None:
    module_ids = default_registry.ids()

    assert len(module_ids) == len(set(module_ids))


def test_module_descriptions_exist() -> None:
    for module in default_registry.all():
        assert module.description.strip()
