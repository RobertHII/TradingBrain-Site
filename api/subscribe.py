"""
TradingBrain Email Subscription - Vercel Serverless Function

Handles email capture for discount code generation.
Stores subscribers in Supabase and returns a unique discount code.

Deployed to: https://tradingbrainz.com/api/subscribe
"""

import os
import json
import secrets
from datetime import datetime
from http.server import BaseHTTPRequestHandler


# Environment variables (set in Vercel dashboard)
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')


def generate_discount_code() -> str:
    """Generate a unique discount code: WELCOME15-XXXXXX"""
    suffix = secrets.token_hex(3).upper()
    return f"WELCOME15-{suffix}"


def save_subscriber(email: str, code: str) -> bool:
    """Save subscriber to Supabase database."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("Supabase not configured - skipping database save")
        return True  # Still return success, just don't save

    try:
        import urllib.request
        import urllib.error

        data = json.dumps({
            "email": email,
            "discount_code": code,
            "code_used": False,
            "subscribed_at": datetime.utcnow().isoformat()
        }).encode('utf-8')

        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/subscribers",
            data=data,
            headers={
                'Content-Type': 'application/json',
                'apikey': SUPABASE_SERVICE_KEY,
                'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
                'Prefer': 'return=minimal'
            },
            method='POST'
        )

        urllib.request.urlopen(req)
        return True

    except urllib.error.HTTPError as e:
        if e.code == 409:  # Conflict - email already exists
            print(f"Email already subscribed: {email}")
            return True  # Still return success
        print(f"Supabase error: {e.code} - {e.read().decode()}")
        return False
    except Exception as e:
        print(f"Error saving subscriber: {e}")
        return False


def get_existing_code(email: str) -> str:
    """Check if email already has a code."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None

    try:
        import urllib.request
        import urllib.parse

        encoded_email = urllib.parse.quote(email)
        url = f"{SUPABASE_URL}/rest/v1/subscribers?email=eq.{encoded_email}&select=discount_code"

        req = urllib.request.Request(
            url,
            headers={
                'apikey': SUPABASE_SERVICE_KEY,
                'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            },
            method='GET'
        )

        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())

        if data and len(data) > 0:
            return data[0].get('discount_code')

        return None

    except Exception as e:
        print(f"Error checking existing code: {e}")
        return None


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler."""

    def do_POST(self):
        """Handle POST request (email subscription)."""
        try:
            # Read body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body)

            email = payload.get('email', '').strip().lower()

            # Validate email
            if not email or '@' not in email or '.' not in email:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid email address"}).encode())
                return

            # Check for existing subscription
            existing_code = get_existing_code(email)
            if existing_code:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "code": existing_code,
                    "message": "Welcome back! Here's your discount code."
                }).encode())
                return

            # Generate new code
            code = generate_discount_code()

            # Save to database
            save_subscriber(email, code)

            # Return success
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "code": code,
                "message": "Thanks for subscribing! Use this code for 15% off."
            }).encode())

        except Exception as e:
            print(f"Subscribe error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """Handle GET request (health check)."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "service": "TradingBrain Email Subscription"
        }).encode())
