"""Service for sending emails via Gmail SMTP."""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from config import Config

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails using Gmail SMTP."""
    
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    
    @classmethod
    async def send_call_summary_email(
        cls,
        to_email: str,
        client_name: str,
        summary: str,
        follow_up_date: Optional[str] = None
    ) -> dict:
        """
        Send a call summary email to the user via Gmail SMTP.
        
        Args:
            to_email: Recipient email address.
            client_name: Name of the client.
            summary: AI-generated call summary.
            follow_up_date: Follow-up date in YYYY-MM-DD format (optional).
            
        Returns:
            dict: Response containing success status and details.
            
        Raises:
            Exception: If email sending fails.
        """
        try:
            # Validate configuration
            gmail_user = Config.GMAIL_USER
            gmail_password = Config.GMAIL_APP_PASSWORD
            from_email = Config.GMAIL_FROM_EMAIL
            
            if not gmail_user or not gmail_password:
                raise ValueError("Gmail SMTP credentials are not configured")
            
            # Build the HTML content
            follow_up_section = ""
            if follow_up_date:
                follow_up_section = f"""
                <div style="background-color: #e8f4fd; padding: 15px; border-radius: 8px; margin-top: 20px;">
                    <h3 style="color: #1a73e8; margin-top: 0;">📅 Scheduled Follow-up</h3>
                    <p style="font-size: 18px; font-weight: bold; color: #333;">{follow_up_date}</p>
                </div>
                """
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">📞 Your Call Summary</h1>
                </div>
                
                <div style="background-color: #f9f9f9; padding: 25px; border-radius: 0 0 10px 10px; border: 1px solid #eee; border-top: none;">
                    <p style="color: #666; margin-top: 0;">Hello {client_name},</p>
                    <p>Thank you for your recent call. Here's a summary of our conversation:</p>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; margin: 20px 0;">
                        <h3 style="color: #667eea; margin-top: 0;">📝 Call Summary</h3>
                        <p style="color: #555;">{summary}</p>
                    </div>
                    
                    {follow_up_section}
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="color: #888; font-size: 12px; margin-bottom: 0;">
                        This is an automated message from DevFuzzion Voice Assistant.<br>
                        If you have any questions, please don't hesitate to call us back.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Plain text fallback
            plain_text = f"""
Hello {client_name},

Thank you for your recent call. Here's a summary of our conversation:

CALL SUMMARY:
{summary}

{"SCHEDULED FOLLOW-UP: " + follow_up_date if follow_up_date else ""}

This is an automated message from DevFuzzion Voice Assistant.
If you have any questions, please don't hesitate to call us back.
            """.strip()
            
            # Create message container
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Your Call Summary - {client_name}"
            msg["From"] = from_email
            msg["To"] = to_email
            
            # Attach plain text and HTML versions
            part1 = MIMEText(plain_text, "plain")
            part2 = MIMEText(html_content, "html")
            msg.attach(part1)
            msg.attach(part2)
            
            # Send via Gmail SMTP
            with smtplib.SMTP(cls.SMTP_SERVER, cls.SMTP_PORT) as server:
                server.starttls()
                server.login(gmail_user, gmail_password)
                server.sendmail(from_email, to_email, msg.as_string())
            
            logger.info(f"[EmailService] Email sent successfully to {to_email}")
            
            return {
                "success": True,
                "email_id": None,  # SMTP doesn't return an ID like Resend
                "to": to_email
            }
            
        except Exception as e:
            logger.error(f"[EmailService] Failed to send email to {to_email}: {e}")
            return {
                "success": False,
                "error": str(e),
                "to": to_email
            }
