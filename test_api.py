"""API tests for the records-request API. Run the server (python app.py), then: pytest -v"""
import pytest, requests

BASE = "http://127.0.0.1:5000/requests"

@pytest.fixture
def new_request():
    r = requests.post(BASE, json={"agency": "Pima County", "subject": "Caseload data"})
    yield r.json()
    requests.delete(f"{BASE}/{r.json()['id']}")

# ---------- positive tests ----------
def test_create_returns_201_and_body():
    r = requests.post(BASE, json={"agency": "Maricopa County", "subject": "Inspection records"})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "submitted" and isinstance(body["id"], int)
    assert r.headers["Content-Type"] == "application/json"
    requests.delete(f"{BASE}/{body['id']}")

def test_get_by_id(new_request):
    r = requests.get(f"{BASE}/{new_request['id']}")
    assert r.status_code == 200
    assert r.json() == new_request

def test_update_status(new_request):
    r = requests.patch(f"{BASE}/{new_request['id']}", json={"status": "in_review"})
    assert r.status_code == 200
    assert requests.get(f"{BASE}/{new_request['id']}").json()["status"] == "in_review"

def test_filter_by_status(new_request):
    requests.patch(f"{BASE}/{new_request['id']}", json={"status": "fulfilled"})
    r = requests.get(BASE, params={"status": "fulfilled"})
    assert r.status_code == 200
    assert all(item["status"] == "fulfilled" for item in r.json())
    assert new_request["id"] in [item["id"] for item in r.json()]

def test_delete_then_get_is_404():
    rid = requests.post(BASE, json={"agency": "Pinal County", "subject": "Policy manual"}).json()["id"]
    assert requests.delete(f"{BASE}/{rid}").status_code == 204
    assert requests.get(f"{BASE}/{rid}").status_code == 404

def test_response_time_under_500ms():
    r = requests.get(BASE)
    assert r.elapsed.total_seconds() < 0.5

# ---------- negative tests ----------
@pytest.mark.parametrize("payload", [{}, {"agency": "Pima County"}, {"subject": "Caseload data"},
                                     {"agency": "", "subject": "x"},
                                     {"agency": "   ", "subject": "x"}])
def test_create_missing_fields_returns_400(payload):
    r = requests.post(BASE, json=payload)
    assert r.status_code == 400
    assert "required" in r.json()["error"]

def test_invalid_status_returns_422(new_request):
    r = requests.patch(f"{BASE}/{new_request['id']}", json={"status": "lost"})
    assert r.status_code == 422

def test_unknown_id_returns_404():
    assert requests.get(f"{BASE}/99999").status_code == 404

def test_wrong_method_returns_405():
    assert requests.put(BASE).status_code == 405
