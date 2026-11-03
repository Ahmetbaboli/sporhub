import ssl

from app.core.tls import ssl_context


def test_ssl_context_still_verifies_certificates_and_hostnames() -> None:
    context = ssl_context()
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
    assert ssl_context() is context
