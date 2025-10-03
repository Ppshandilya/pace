# generate_secret.py
import secrets

# produce a URL-safe, random secret ~43 chars (suitable for HS256)
secret = secrets.token_urlsafe(32)
print(secret)


