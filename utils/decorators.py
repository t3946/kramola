import functools
from typing import Callable

from flask import request, redirect, url_for


def require_query_params(*param_names: str, redirect_endpoint: str) -> Callable:
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if any(not request.args.get(p) for p in param_names):
                return redirect(url_for(redirect_endpoint))
            return f(*args, **kwargs)
        return wrapped
    return decorator
