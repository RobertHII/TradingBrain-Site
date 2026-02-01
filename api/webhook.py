"""
TradingBrain Payment Webhook - Vercel Serverless Function

This handles NOWPayments IPN callbacks for tradingbrainz.com
Deployed to: https://tradingbrainz.com/api/webhook

To use with Vercel:
1. Install Vercel CLI: npm i -g vercel
2. Run: vercel --prod
"""

import os
import json
import hmac
import hashlib
import smtplib
import secrets
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from http.server import BaseHTTPRequestHandler


# Environment variables (set in Vercel dashboard)
NOWPAYMENTS_IPN_SECRET = os.environ.get('NOWPAYMENTS_IPN_SECRET', '')
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')
LICENSE_SMTP_SERVER = os.environ.get('LICENSE_SMTP_SERVER', 'smtp.zoho.com')
LICENSE_SMTP_PORT = int(os.environ.get('LICENSE_SMTP_PORT', '587'))
LICENSE_SMTP_USER = os.environ.get('LICENSE_SMTP_USER', '')
LICENSE_SMTP_PASSWORD = os.environ.get('LICENSE_SMTP_PASSWORD', '')
LICENSE_FROM_EMAIL = os.environ.get('LICENSE_FROM_EMAIL', '')


def generate_license_key() -> str:
    """Generate a license key in format TB-XXXX-XXXX-XXXX-XXXX."""
    parts = [secrets.token_hex(2).upper() for _ in range(4)]
    return f"TB-{'-'.join(parts)}"


def verify_signature(payload: dict, signature: str) -> bool:
    """Verify NOWPayments IPN signature."""
    if not NOWPAYMENTS_IPN_SECRET or not signature:
        return False

    sorted_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    expected_sig = hmac.new(
        NOWPAYMENTS_IPN_SECRET.encode('utf-8'),
        sorted_payload.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

    return hmac.compare_digest(expected_sig, signature)


def send_license_email(email: str, license_key: str, tier: str) -> bool:
    """Send license key to customer via email."""
    if not all([LICENSE_SMTP_USER, LICENSE_SMTP_PASSWORD, LICENSE_FROM_EMAIL]):
        print("Email not configured")
        return False

    tier_name = "Bot-Only License" if tier == "BOT_ONLY" else "Full System License"

    subject = f"Your TradingBrain {tier_name} - License Key"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #0d1117; color: #c9d1d9; padding: 40px;">
        <div style="max-width: 600px; margin: 0 auto; background: #161b22; border-radius: 12px; padding: 40px; border: 1px solid #30363d;">
            <h1 style="color: #58a6ff; margin-bottom: 20px;">Thank You for Your Purchase!</h1>

            <p>Your TradingBrain <strong>{tier_name}</strong> has been activated.</p>

            <div style="background: #0d1117; border: 2px solid #238636; border-radius: 8px; padding: 20px; margin: 30px 0; text-align: center;">
                <p style="color: #8b949e; margin-bottom: 10px;">Your License Key:</p>
                <p style="font-size: 24px; font-family: monospace; color: #58a6ff; letter-spacing: 2px; margin: 0;">
                    <strong>{license_key}</strong>
                </p>
            </div>

            <h3 style="color: #c9d1d9;">Getting Started:</h3>
            <ol style="color: #8b949e; line-height: 1.8;">
                <li>Download TradingBrain from your purchase confirmation</li>
                <li>Run the application and go to Settings > License</li>
                <li>Enter your license key above</li>
                <li>Start building your trading edge!</li>
            </ol>

            <p style="color: #8b949e; margin-top: 30px;">
                Need help? Reply to this email or visit our support page.
            </p>

            <hr style="border: none; border-top: 1px solid #30363d; margin: 30px 0;">

            <p style="color: #6e7681; font-size: 12px;">
                This is an automated message from TradingBrainz.com<br>
                Keep this email for your records.
            </p>
        </div>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = LICENSE_FROM_EMAIL
        msg['To'] = email

        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(LICENSE_SMTP_SERVER, LICENSE_SMTP_PORT) as server:
            server.starttls()
            server.login(LICENSE_SMTP_USER, LICENSE_SMTP_PASSWORD)
            server.sendmail(LICENSE_FROM_EMAIL, email, msg.as_string())

        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def save_to_supabase(license_key: str, tier: str, email: str, payment_id: str) -> bool:
    """Save license to Supabase cloud database."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("Supabase not configured")
        return False

    try:
        import urllib.request
        import urllib.error

        # Create user
        user_data = json.dumps({"email": email}).encode('utf-8')
        user_req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/users",
            data=user_data,
            headers={
                'Content-Type': 'application/json',
                'apikey': SUPABASE_SERVICE_KEY,
                'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
                'Prefer': 'return=representation'
            },
            method='POST'
        )

        try:
            urllib.request.urlopen(user_req)
        except urllib.error.HTTPError:
            pass  # User might already exist

        # Create license
        license_data = json.dumps({
            "license_key": license_key,
            "tier": tier,
            "is_active": True,
            "metadata": {"payment_id": payment_id, "customer_email": email}
        }).encode('utf-8')

        license_req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/licenses",
            data=license_data,
            headers={
                'Content-Type': 'application/json',
                'apikey': SUPABASE_SERVICE_KEY,
                'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
                'Prefer': 'return=representation'
            },
            method='POST'
        )

        urllib.request.urlopen(license_req)
        return True

    except Exception as e:
        print(f"Supabase error: {e}")
        return False


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler."""

    def do_POST(self):
        """Handle POST request (IPN callback)."""
        try:
            # Read body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body)

            # Get signature
            signature = self.headers.get('x-nowpayments-sig', '')

            # Verify signature
            if not verify_signature(payload, signature):
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid signature"}).encode())
                return

            # Check payment status
            status = payload.get('payment_status', '')

            if status in ('finished', 'confirmed'):
                payment_id = str(payload.get('payment_id', ''))
                order_id = payload.get('order_id', '')

                # Extract tier and email from order_id or payload
                tier = 'BOT_ONLY'
                if 'FULL' in order_id:
                    tier = 'FULL'

                email = payload.get('customer_email', '')
                if not email:
                    # Try to extract from order description
                    email = payload.get('order_description', '').split('|')[-1].strip()

                if email:
                    # Generate license
                    license_key = generate_license_key()

                    # Save to Supabase
                    save_to_supabase(license_key, tier, email, payment_id)

                    # Send email
                    send_license_email(email, license_key, tier)

                    print(f"License generated: {license_key} for {email}")

            # Success response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode())

        except Exception as e:
            print(f"Webhook error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        """Handle GET request (health check)."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "service": "TradingBrain Payment Webhook"
        }).encode())
