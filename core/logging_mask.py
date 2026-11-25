import re


SENSITIVE_FIELD = re.compile(
    r"""(?P<key>\b(?:phone|email|password|otp|token|authorization|cookie|sessid)\b["']?\s*[:=]\s*)"""
    r"""(?:"[^"\r\n]*"|'[^'\r\n]*'|(?:bearer\s+)?[^\s,;]+)""",
    re.IGNORECASE,
)


def mask_credentials(message):
    return SENSITIVE_FIELD.sub(r"\g<key>***", message)
