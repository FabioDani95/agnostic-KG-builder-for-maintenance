from fastapi.routing import APIRoute

from backend.main import create_app


def _api_routes(app):
    return [route for route in app.routes if isinstance(route, APIRoute)]


def test_step_wise_legacy_routes_are_not_mounted_by_default(monkeypatch):
    monkeypatch.delenv("KG_ENABLE_LEGACY_ROUTES", raising=False)

    paths = {route.path for route in _api_routes(create_app())}

    assert "/cut-plan" not in paths
    assert "/cut-plan/approve" not in paths
    assert "/extract-tables" not in paths
    assert "/ontology/draft" not in paths
    assert "/generate-json" in paths


def test_step_wise_legacy_routes_mount_only_behind_flag(monkeypatch):
    monkeypatch.setenv("KG_ENABLE_LEGACY_ROUTES", "1")

    routes = _api_routes(create_app())
    by_path = {route.path: route for route in routes}

    assert by_path["/cut-plan"].deprecated is True
    assert by_path["/cut-plan/approve"].deprecated is True
    assert by_path["/extract-tables"].deprecated is True
    assert by_path["/ontology/draft"].deprecated is True
    assert by_path["/generate-json"].deprecated is None
