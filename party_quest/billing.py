from __future__ import annotations

import os
import re
from urllib.parse import urlparse


class BillingConfigurationError(RuntimeError):
    pass


def public_origin(request_origin: str) -> str:
    configured = os.getenv("APP_URL", "").strip().rstrip("/")
    if configured:
        parsed = urlparse(configured)
        if parsed.scheme != "https" or not parsed.netloc:
            raise BillingConfigurationError("APP_URL must be a valid HTTPS origin.")
        return configured
    parsed = urlparse(request_origin)
    if parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}:
        return request_origin.rstrip("/")
    raise BillingConfigurationError("APP_URL is required before checkout can be enabled.")


def _valid_install_id(install_id: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_-]{16,96}", install_id))


def create_checkout(origin: str, install_id: str) -> str:
    secret = os.getenv("STRIPE_SECRET_KEY", "").strip()
    price = os.getenv("STRIPE_PRICE_LIFETIME", "").strip()
    if not secret or not price:
        raise BillingConfigurationError("Lifetime checkout is not configured yet.")
    if not _valid_install_id(install_id):
        raise ValueError("A valid browser installation ID is required.")
    import stripe
    stripe.api_key = secret
    target = public_origin(origin)
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price": price, "quantity": 1}],
        allow_promotion_codes=True,
        success_url=f"{target}/?checkout=success&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{target}/?checkout=cancelled",
        metadata={"app": "party-quest-maker", "license": "lifetime-browser", "install_id": install_id},
    )
    if not session.url:
        raise RuntimeError("Stripe did not return a checkout URL.")
    return session.url


def _session_is_entitled(session: object, expected_price: str, install_id: str) -> bool:
    metadata = session.get("metadata") or {}
    line_items = (session.get("line_items") or {}).get("data") or []
    price_id = line_items[0].get("price", {}).get("id") if len(line_items) == 1 else None
    payment_intent = session.get("payment_intent") or {}
    charge = payment_intent.get("latest_charge") or {}
    return all((
        session.get("mode") == "payment",
        session.get("status") == "complete",
        session.get("payment_status") == "paid",
        metadata.get("app") == "party-quest-maker",
        metadata.get("license") == "lifetime-browser",
        metadata.get("install_id") == install_id,
        price_id == expected_price,
        not charge.get("refunded", False),
        int(charge.get("amount_refunded", 0) or 0) == 0,
        not charge.get("disputed", False),
    ))


def verify_entitlement(session_id: str, install_id: str) -> dict[str, object]:
    if not session_id.startswith("cs_") or len(session_id) > 256:
        return {"active": False, "reason": "invalid_session"}
    if not _valid_install_id(install_id):
        return {"active": False, "reason": "invalid_installation"}
    secret = os.getenv("STRIPE_SECRET_KEY", "").strip()
    expected_price = os.getenv("STRIPE_PRICE_LIFETIME", "").strip()
    if not secret or not expected_price:
        raise BillingConfigurationError("Purchase verification is not configured yet.")
    import stripe
    stripe.api_key = secret
    session = stripe.checkout.Session.retrieve(
        session_id,
        expand=["line_items.data.price", "payment_intent.latest_charge"],
    )
    active = _session_is_entitled(session, expected_price, install_id)
    return {"active": active, "license": "lifetime" if active else "none"}
