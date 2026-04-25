"""
core/mailer.py — SMTP email dispatch for Aurus Jewels.
Sends order confirmation + invoice PDF to customer.
"""
import smtplib, os, sys
from email.mime.multipart  import MIMEMultipart
from email.mime.text       import MIMEText
from email.mime.application import MIMEApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
from database.db import execute_write


def send_invoice_email(
    to_email:       str,
    customer_name:  str,
    order_id:       int,
    invoice_number: str,
    invoice_path:   str | None
) -> bool:
    """
    Send order confirmation email with invoice PDF attached.
    Returns True on success, False on failure.
    """
    if not config.SMTP_USER or not config.SMTP_PASS:
        _log(to_email,
             f"Order #{order_id} Confirmed",
             "failed",
             "SMTP credentials not configured")
        return False

    try:
        msg = MIMEMultipart("mixed")
        msg["From"]    = (
            f"{config.SMTP_FROM_NAME} <{config.SMTP_USER}>"
        )
        msg["To"]      = to_email
        msg["Subject"] = (
            f"Your Aurus Jewels Order #{order_id} "
            f"is Confirmed — {invoice_number}"
        )

        # ── HTML body ────────────────────────────────────────
        html = f"""
        <html>
        <body style="font-family:Arial,sans-serif;
                     background:#FFFDF9;
                     color:#1A1008;
                     padding:32px;">

          <div style="max-width:560px;margin:0 auto;">

            <h1 style="font-size:22px;color:#B8860B;
                       letter-spacing:.08em;margin-bottom:4px;">
              ⬡ AURUS JEWELS
            </h1>
            <p style="font-size:12px;color:#8B6914;
                      margin-bottom:24px;">
              Fine Hallmarked Gold & Silver Jewellery
            </p>

            <p style="font-size:15px;">Dear {customer_name},</p>
            <p style="font-size:14px;line-height:1.7;">
              Thank you for your order! Your order
              <strong>#{order_id}</strong> has been
              confirmed successfully.
            </p>

            <div style="background:#FFF8EE;
                        border:1px solid #E8D5A3;
                        border-radius:6px;
                        padding:16px 20px;
                        margin:20px 0;">
              <p style="font-size:13px;margin:0 0 6px;">
                <strong>Invoice Number:</strong>
                {invoice_number}
              </p>
              <p style="font-size:13px;margin:0;color:#8B6914;">
                Your GST invoice is attached to this email.
              </p>
            </div>

            <p style="font-size:13px;color:#4A3728;
                      line-height:1.7;">
              All your products are
              <strong>BIS hallmarked</strong> and priced
              transparently from the official IBJA gold rate.
              You can track your order status anytime from
              <strong>My Account → My Orders</strong>.
            </p>

            <div style="margin-top:28px;
                        padding-top:16px;
                        border-top:1px solid #E8D5A3;">
              <p style="font-size:11px;color:#8B6914;">
                © 2026 Aurus Jewels &nbsp;|&nbsp;
                GSTIN: {config.GSTIN}
              </p>
              <p style="font-size:11px;color:#8B6914;">
                Prices update daily from the IBJA
                official gold rate.
              </p>
            </div>

          </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))

        # ── Attach invoice PDF ────────────────────────────────
        if invoice_path and os.path.exists(invoice_path):
            with open(invoice_path, "rb") as f:
                attachment = MIMEApplication(
                    f.read(), _subtype="pdf"
                )
                attachment.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=os.path.basename(invoice_path)
                )
                msg.attach(attachment)

        # ── Send ─────────────────────────────────────────────
        with smtplib.SMTP(
            config.SMTP_HOST, config.SMTP_PORT
        ) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASS)
            server.sendmail(
                config.SMTP_USER,
                to_email,
                msg.as_string()
            )

        _log(to_email, msg["Subject"], "sent")
        return True

    except Exception as e:
        _log(
            to_email,
            f"Order #{order_id} Confirmed",
            "failed",
            str(e)
        )
        return False


def _log(
    to_email: str,
    subject:  str,
    status:   str,
    error:    str = ""
):
    """Log email attempt to email_log table."""
    execute_write(
        """INSERT INTO email_log
             (to_email, subject, status, error_message)
           VALUES (%s, %s, %s, %s)""",
        (to_email, subject, status, error)
    )