"""Registry service: dynamic tables, typed validation, import/export."""


import pytest

from glassy_app.core.errors import ConflictError, ValidationError
from glassy_app.services.registries import BUILTIN_TEMPLATES


def test_create_from_every_template(empty_app):
    for key in BUILTIN_TEMPLATES:
        registry_id = empty_app.registries.create_from_template(key)
        registry = empty_app.registries.get_registry(registry_id)
        assert registry["fields"], f"{key} has no fields"
        assert registry["title"]


def test_duplicate_name_is_rejected(app):
    app.registries.create_registry(name="mine", title="Mine")
    with pytest.raises(ConflictError):
        app.registries.create_registry(name="mine", title="Again")


def test_invalid_name_is_rejected(app):
    with pytest.raises(ValidationError):
        app.registries.create_registry(name="bad name!", title="x")


def test_typed_values_are_validated(app):
    registry_id = app.registries.create_registry(
        name="t", title="T", template="inventory"
    )
    app.registries.add_record(
        registry_id,
        {"name": "Drill", "qty": "2", "price": "19.99", "bought": "2026-02-03"},
    )
    _registry, rows = app.registries.display_rows(registry_id)
    assert rows[0]["display"]["name"] == "Drill"
    assert rows[0]["display"]["price"] == "19.99\u00a0\u20bd"
    assert rows[0]["display"]["bought"] == "2026-02-03"
    # money is stored as integer minor units, so it can be summed exactly
    assert rows[0]["data"]["price"] == "1999"


@pytest.mark.parametrize(
    "payload",
    [
        {"price": "abc"},
        {"bought": "not-a-date"},
        {"qty": "many"},
    ],
)
def test_bad_values_are_rejected(app, payload):
    registry_id = app.registries.create_registry(
        name="t", title="T", template="inventory"
    )
    data = {"name": "ok"}
    data.update(payload)
    with pytest.raises(ValidationError):
        app.registries.add_record(registry_id, data)


def test_required_field_is_enforced(app):
    registry_id = app.registries.create_registry(
        name="t", title="T", template="inventory"
    )
    with pytest.raises(ValidationError):
        app.registries.add_record(registry_id, {"qty": "1"})


def test_money_total_is_exact(app):
    registry_id = app.registries.create_registry(
        name="t", title="T", template="inventory"
    )
    app.registries.add_record(registry_id, {"name": "a", "price": "0.10"})
    app.registries.add_record(registry_id, {"name": "b", "price": "0.20"})
    assert app.registries.numeric_total(registry_id, "price") == 30


def test_search_filters_records(app):
    registry_id = app.registries.create_registry(
        name="t", title="T", template="inventory"
    )
    app.registries.add_record(registry_id, {"name": "Hammer"})
    app.registries.add_record(registry_id, {"name": "Saw"})
    _r, rows = app.registries.display_rows(registry_id, search="Hammer")
    assert len(rows) == 1


def test_adding_a_column_keeps_existing_records(app):
    registry_id = app.registries.create_registry(
        name="t", title="T", template="contacts"
    )
    app.registries.add_record(registry_id, {"name": "Ann", "phone": "1"})
    app.registries.add_field(registry_id, "city", "City", "text")
    _registry, rows = app.registries.display_rows(registry_id)
    assert rows[0]["data"]["name"] == "Ann"
    assert rows[0]["display"]["city"] == ""


def test_duplicate_field_key_is_rejected(app):
    registry_id = app.registries.create_registry(
        name="t", title="T", template="contacts"
    )
    with pytest.raises(ConflictError):
        app.registries.add_field(registry_id, "name", "Another")


def test_export_csv_has_header_and_rows(app):
    registry_id = app.registries.create_registry(
        name="t", title="T", template="inventory"
    )
    app.registries.add_record(registry_id, {"name": "Drill", "qty": "1"})
    csv_text = app.registries.export_csv(registry_id)
    lines = csv_text.strip().splitlines()
    assert lines[0].startswith("Item,Qty")
    assert "Drill" in lines[1]


def test_json_round_trip_into_a_second_database(data_dir):
    from glassy_app.app import Application

    first = Application(data_dir=data_dir / "one")
    registry_id = first.registries.create_registry(
        name="t", title="T", template="inventory"
    )
    first.registries.add_record(registry_id, {"name": "Drill", "price": "9.99"})
    payload = first.registries.export_json(registry_id)
    first.close()

    second = Application(data_dir=data_dir / "two", seed=False)
    new_id, imported = second.registries.import_json(payload)
    assert imported == 1
    _registry, rows = second.registries.display_rows(new_id)
    assert rows[0]["data"]["name"] == "Drill"
    assert rows[0]["data"]["price"] == "999"
    second.close()


def test_import_is_idempotent_into_same_registry(app):
    registry_id = app.registries.create_registry(
        name="t", title="T", template="inventory"
    )
    app.registries.add_record(registry_id, {"name": "Drill"})
    payload = app.registries.export_json(registry_id)
    same_id, imported = app.registries.import_json(payload)
    assert same_id == registry_id
    assert imported == 1
    assert len(app.registries.list_records(registry_id)) == 2


def test_delete_registry_removes_records(app):
    registry_id = app.registries.create_registry(
        name="t", title="T", template="contacts"
    )
    app.registries.add_record(registry_id, {"name": "Ann"})
    app.registries.delete_registry(registry_id)
    assert app.registries.list_registries() == []
    assert app.registries.list_records(registry_id) == []
