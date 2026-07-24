from datetime import datetime, timedelta, timezone

import pytest

from bluejet_api.finance import SandboxLightningGateway


def _token(amount_sats=1000, expires_at=None, payment_hash="a" * 64):
    expires_at = expires_at or datetime.now(timezone.utc) + timedelta(minutes=5)
    return f"lnsbx:regtest:{amount_sats}:{int(expires_at.timestamp())}:{payment_hash}"


def test_sandbox_invoice_validator_returns_only_sanitized_metadata():
    metadata = SandboxLightningGateway().validate_invoice(_token(), 1000)

    assert metadata["network"] == "regtest"
    assert metadata["amount_sats"] == 1000
    assert metadata["payment_hash"] == "a" * 64
    assert len(metadata["invoice_hash"]) == 64
    assert "invoice" not in metadata


@pytest.mark.parametrize(
    "invoice, expected_sats",
    [
        ("lnbc-real-looking", 1000),
        (_token(amount_sats=999), 1000),
        (_token(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)), 1000),
        (_token(payment_hash="not-hex"), 1000),
    ],
)
def test_sandbox_invoice_validator_fails_closed(invoice, expected_sats):
    with pytest.raises(ValueError):
        SandboxLightningGateway().validate_invoice(invoice, expected_sats)
