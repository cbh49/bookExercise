from functools import wraps
import hashlib
import json
from flask import request, abort
from services.cache_service import cache

def prevent_replay(user_id, expiration_time=60):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            request_data = {
                'path': request.path,
                'method': request.method,
                'data': request.get_data().decode('utf-8'),
                'user_id': user_id,
                'headers': dict(request.headers)
            }

            request_hash = hashlib.sha256(
                json.dumps(request_data, sort_keys=True).encode()
            ).hexdigest()

            cache_key = f"request:{user_id}:{request_hash}"

            if cache.get(cache_key):
                abort(409, description="Duplicate request detected")

            cache.setex(cache_key, expiration_time, 'seen')

            rate_limit_key = f"rate_limit:{user_id}"
            current_requests = cache.get(rate_limit_key)

            if current_requests and int(current_requests) > 1000:
                abort(429, description="Too many requests")
            
            cache.incr(rate_limit_key)
            cache.expire(rate_limit_key, 1)

            return f(*args, **kwargs)
        return decorated_function
    return decorator