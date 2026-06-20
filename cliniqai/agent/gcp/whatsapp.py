import os
import logging

logger = logging.getLogger(__name__)

def send_whatsapp_alert(phone_number: str, message_body: str):
    """
    Sends a WhatsApp message using Twilio's API.
    For the hackathon, this uses the Twilio Sandbox. 
    If TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are not set, it mocks the sending.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_whatsapp_number = 'whatsapp:+14155238886' # Standard Twilio Sandbox Number
    
    # Ensure phone number has country code. Defaulting to India (+91) for Bharat Academix
    clean_phone = phone_number.replace(" ", "").replace("+", "")
    if not clean_phone.startswith("91") and len(clean_phone) == 10:
        clean_phone = f"91{clean_phone}"
        
    to_whatsapp_number = f'whatsapp:+{clean_phone}'

    if not account_sid or not auth_token:
        logger.warning(f"🚀 [MOCK WHATSAPP SENT] To {to_whatsapp_number}: \n{message_body}")
        return True

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message_body,
            from_=from_whatsapp_number,
            to=to_whatsapp_number
        )
        logger.info(f"✅ WhatsApp successfully sent! Message SID: {message.sid}")
        return True
    except ImportError:
        logger.error("twilio library not installed. Run: pip install twilio")
        return False
    except Exception as e:
        logger.error(f"Failed to send WhatsApp: {e}")
        return False
