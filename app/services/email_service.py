from mailjet_rest import Client
from app.core.config import get_settings
from pathlib import Path
from datetime import datetime, timedelta
import jinja2

settings = get_settings()
mailjet = Client(auth=(settings.MAILJET_API_KEY, settings.MAILJET_SECRET_KEY), version='v3.1')

# Setup Jinja2 template environment
template_dir = Path(__file__).parent.parent / "templates"
template_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(template_dir))
)

def send_verification_email(user_email: str, user_name: str, verification_token: str) -> None:
    """Send verification email to user."""
    try:
        # Get the verification template
        template = template_env.get_template("email/verification.html")
        
        # Generate verification URL
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        
        # Render the template
        html_content = template.render(
            user_name=user_name,
            verification_url=verification_url
        )
        
        # Prepare email data
        data = {
            'Messages': [
                {
                    "From": {
                        "Email": settings.MAIL_FROM,
                        "Name": settings.MAIL_FROM_NAME
                    },
                    "To": [
                        {
                            "Email": user_email,
                            "Name": user_name
                        }
                    ],
                    "Subject": "Verify your email - VidGen",
                    "HTMLPart": html_content
                }
            ]
        }
        
        # Send the email
        result = mailjet.send.create(data=data)
        
        if result.status_code > 299:
            print(f"Failed to send email: {result.json()}")
            raise Exception("Failed to send verification email")
            
    except Exception as e:
        print(f"Error sending verification email: {str(e)}")
        raise 