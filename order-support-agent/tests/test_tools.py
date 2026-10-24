from agent.tools import get_order_status, get_return_policy, run_tool, search_products


def test_order_ok():
    data = get_order_status("ord-1001", "4321")
    assert data["status"] == "shipped" and "phone_last4" not in data


def test_order_wrong_phone_leaks_nothing():
    data = get_order_status("ORD-1001", "0000")
    assert "error" in data and "tracking_number" not in data


def test_order_unknown_same_error_as_wrong_phone():
    assert get_order_status("ORD-9999", "1234") == get_order_status("ORD-1001", "0000")


def test_search_products():
    names = [p["name"] for p in search_products("strong morning tea")["results"]]
    assert names and "Assam" in names[0]


def test_policy():
    assert "7 days" in get_return_policy()["policy"]


def test_run_tool_never_raises():
    assert "error" in run_tool("nope", {})
    assert "error" in run_tool("get_order_status", {"wrong": 1})
