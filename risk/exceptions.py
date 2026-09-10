"""
Consistent error response shape for the whole API.

Without this, DRF's default validation errors, 404s, and auth errors
each come back in a different shape. The frontend needs one predictable
shape to handle errors generically instead of writing a special case
per endpoint.

Every error response looks like:
    {
        "error": {
            "code": "validation_error" | "not_found" | "authentication_failed" | ...,
            "message": "Human-readable summary.",
            "details": {...}   # optional, e.g. field-level validation errors
        }
    }
"""
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    code = getattr(exc, 'default_code', exc.__class__.__name__.lower())
    detail = response.data

    if isinstance(detail, dict):
        message = detail.get('detail') or 'One or more fields failed validation.'
        details = detail if 'detail' not in detail else None
    elif isinstance(detail, list):
        message = 'One or more fields failed validation.'
        details = detail
    else:
        message = str(detail)
        details = None

    response.data = {
        'error': {
            'code': code,
            'message': message,
            **({'details': details} if details else {}),
        }
    }
    return response
