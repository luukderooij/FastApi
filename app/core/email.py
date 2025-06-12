import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ..config import settings
import logging

logger = logging.getLogger(__name__)

def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Stuurt een email met de opgegeven parameters
    """
    try:
        # Email bericht configureren
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.MAIL_FROM
        message["To"] = to_email
        
        # HTML en tekst gedeelten toevoegen
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Verbinding maken met de SMTP server
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            server.sendmail(settings.MAIL_FROM, to_email, message.as_string())
        
        logger.info(f"Email verzonden naar {to_email}")
        return True
    
    except Exception as e:
        logger.error(f"Fout bij verzenden email: {str(e)}")
        return False

def send_activation_email(user_email: str, token: str) -> bool:
    """
    Stuur een activatie-email naar een nieuwe gebruiker
    """
    activation_link = f"{settings.FRONTEND_URL}/activate?token={token}"
    
    subject = f"Activeer je account bij {settings.PROJECT_NAME}"
    html_content = f"""
    <html>
        <body>
            <h2>Welkom bij {settings.PROJECT_NAME}!</h2>
            <p>Bedankt voor je registratie. Klik op de onderstaande link om je account te activeren:</p>
            <p><a href="{activation_link}">Activeer mijn account</a></p>
            <p>Of kopieer deze URL in je browser: {activation_link}</p>
            <p>Deze link verloopt na 24 uur.</p>
            <p>Als je deze e-mail niet hebt aangevraagd, kun je deze negeren.</p>
        </body>
    </html>
    """
    
    return send_email(user_email, subject, html_content)

def send_password_reset_email(user_email: str, token: str) -> bool:
    """
    Stuur een e-mail met wachtwoordherstel link
    """
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    subject = f"Wachtwoord herstellen voor {settings.PROJECT_NAME}"
    html_content = f"""
    <html>
        <body>
            <h2>Wachtwoord herstellen</h2>
            <p>We hebben een verzoek ontvangen om je wachtwoord te herstellen. Klik op de onderstaande link om een nieuw wachtwoord in te stellen:</p>
            <p><a href="{reset_link}">Nieuw wachtwoord instellen</a></p>
            <p>Of kopieer deze URL in je browser: {reset_link}</p>
            <p>Deze link verloopt na 1 uur.</p>
            <p>Als je geen wachtwoordherstel hebt aangevraagd, kun je deze e-mail negeren.</p>
        </body>
    </html>
    """
    
    return send_email(user_email, subject, html_content)