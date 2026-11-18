import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / name / "handler.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FakeTable:
    def __init__(self):
        self.items = []

    def put_item(self, Item):
        self.items.append(Item)


def test_leave_ok_and_missing():
    m = load("submit_leave")
    t = FakeTable()
    m.table = lambda: t
    out = m.lambda_handler({"employee_name": "John Smith", "startDate": "2026-07-15", "endDate": "2026-07-18"}, None)
    assert out["status"] == "ok" and t.items[0]["employee_name"] == "John Smith"
    assert m.lambda_handler({"employee_name": "John Smith"}, None)["status"] == "error"


def test_benefits_validation():
    m = load("submit_benefits")
    t = FakeTable()
    m.table = lambda: t
    ok = m.lambda_handler({"employee_name": "Jane Doe", "benefit_type": "medical", "claim_amount": 250}, None)
    assert ok["status"] == "ok" and int(t.items[0]["claim_amount"]) == 250
    assert m.lambda_handler({"employee_name": "Jane Doe", "benefit_type": "medical", "claim_amount": -5}, None)["status"] == "error"
    assert m.lambda_handler({"employee_name": "Jane Doe", "benefit_type": "medical", "claim_amount": "abc"}, None)["status"] == "error"


def test_mock_kb_and_routing():
    import sys
    sys.path.insert(0, str(ROOT / "local"))
    import mock_agent
    import mock_kb

    assert "15 days" in mock_kb.answer("How many vacation days do I get as a new hire?")
    assert "two weeks in advance" in mock_kb.answer("How early must I request time off?")
    assert "contact HR" in mock_kb.answer("What is the capital of France?")
    assert "15 days" in mock_agent.route("How many vacation days do I get as a new hire?")
    assert "submitted" in mock_agent.route("Submit a leave request for John Smith, starting 2026-07-15 and ending 2026-07-18.")
