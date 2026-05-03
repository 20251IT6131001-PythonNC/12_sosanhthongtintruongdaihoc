"""
Rate limiting utility.
Uses slowapi (built on the `limits` library) to throttle sensitive endpoints.

Key limits applied in auth router:
  - POST /signup               : 3 requests / minute  (chặn spam tạo tài khoản)
  - POST /verify-signup-code   : 5 requests / 10 min  (chặn brute-force OTP)
  - POST /login                : 10 requests / minute (chặn brute-force mật khẩu)
  - POST /forgot-password/*    : 3–5 requests / 10 min
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Key function: rate-limit by client IP address.
# In production behind a reverse proxy, ensure the real IP is forwarded
# (X-Forwarded-For / X-Real-IP) so the proxy IP is not used as key.
limiter = Limiter(key_func=get_remote_address)
