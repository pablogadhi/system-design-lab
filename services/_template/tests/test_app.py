from fastapi.testclient import TestClient

from __MODULE__.main import app


def test_health():
    client = TestClient(app)
    assert client.get("/healthz").json() == {"status": "ok"}


# Once design/contracts/openapi/__SERVICE__.yaml exists:
# from sdl_common.contract import assert_implements_contract
#
# def test_matches_contract():
#     assert_implements_contract(app, "__SERVICE__")
