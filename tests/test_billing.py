import pytest

from party_quest.billing import BillingConfigurationError, _session_is_entitled, public_origin, verify_entitlement


def test_local_origin_allowed(monkeypatch):
    monkeypatch.delenv("APP_URL", raising=False)
    assert public_origin("http://127.0.0.1:8802") == "http://127.0.0.1:8802"


def test_remote_origin_requires_configuration(monkeypatch):
    monkeypatch.delenv("APP_URL", raising=False)
    with pytest.raises(BillingConfigurationError):
        public_origin("https://attacker.example")


def test_invalid_session_rejected():
    assert verify_entitlement("bad", "browser_install_123456") == {"active": False, "reason": "invalid_session"}


def entitled_session():
    return {
        "mode": "payment", "status": "complete", "payment_status": "paid",
        "metadata": {"app": "party-quest-maker", "license": "lifetime-browser", "install_id": "browser_install_123456"},
        "line_items": {"data": [{"price": {"id": "price_party"}}]},
        "payment_intent": {"latest_charge": {"refunded": False, "amount_refunded": 0, "disputed": False}},
    }


def test_entitlement_matches_app_price_and_installation():
    assert _session_is_entitled(entitled_session(), "price_party", "browser_install_123456")


@pytest.mark.parametrize("mutation", [
    lambda session: session["metadata"].update({"app": "another-app"}),
    lambda session: session["metadata"].update({"install_id": "another_install_123456"}),
    lambda session: session["line_items"]["data"][0]["price"].update({"id": "price_other"}),
    lambda session: session["payment_intent"]["latest_charge"].update({"refunded": True}),
])
def test_entitlement_rejects_wrong_or_revoked_purchase(mutation):
    session = entitled_session()
    mutation(session)
    assert not _session_is_entitled(session, "price_party", "browser_install_123456")
