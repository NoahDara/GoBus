from django.core.mail import send_mail, get_connection
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend



class EmailService:
    def __init__(self, connection: BaseEmailBackend = None):
        """
        Initialize EmailService with optional connection.
        
        Args:
            connection: Optional pre-configured email backend connection
        """
        self.connection = connection

    def send_email(
        self,
        subject: str,
        message: str,
        recipient_list: list,
        from_email: str = None,
        html_message: str = None,
        fail_silently: bool = False,
    ):
        """
        Send email using active mail config or default Django settings.
        """
        task_manager = settings.TASK_MANAGER

        def wrapped_send_email():
            try:
                # Get connection from active config or use default
                connection = self._get_connection()
                from_email_to_use = from_email or self.get_default_from_email()

                settings.LOGGER.debug(
                    f"Sending email to {recipient_list} with subject {subject}"
                )

                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email_to_use,
                    recipient_list=recipient_list,
                    html_message=html_message,
                    fail_silently=fail_silently,
                    connection=connection,
                )
            except Exception as e:
                settings.LOGGER.error(f"Primary email sending failed: {e}")
                self._send_fallback_email(
                    subject=subject,
                    message=message,
                    from_email=from_email or self.get_default_from_email(),
                    recipient_list=recipient_list,
                    html_message=html_message,
                )

        task_manager.run_task(
            func=wrapped_send_email,
            args=[],
            kwargs={},
            callbacks=[],
            error_callbacks=[],
            context={},
        )

    def _get_connection(self):
        """
        Get email connection from active config or default settings.
        
        Returns:
            Email backend connection
        """
        if self.connection:
            return self.connection

        
        # Fall back to default Django email configuration
        return get_connection()

    def get_default_from_email(self):
        """
        Get default from_email from active config or settings.
        
        Returns:
            Email address to use as sender
        """

        
        return settings.DEFAULT_FROM_EMAIL

    def _send_fallback_email(
        self,
        subject: str,
        message: str,
        from_email: str,
        recipient_list: list,
        html_message: str = None,
    ):
        """Send fallback email using hardcoded Office365 configuration."""
        fallback_connection = get_connection(
            host="smtp.office365.com",
            port=587,
            username="",
            password="",
            use_tls=True,
        )
        try:
            send_mail(
                subject=f"[Fallback] {subject}",
                message=f"Original message:\n\n{message}",
                from_email=from_email,
                recipient_list=["admin@daarahtech.com", "admin@daarahtech.com"],
                html_message=f"<h2>Email Fallback Notice</h2><br>{html_message or message}",
                fail_silently=False,
                connection=fallback_connection,
            )
            settings.LOGGER.info("Fallback email sent successfully.")
        except Exception as e:
            settings.LOGGER.critical(f"Fallback email sending failed: {e}")


def get_email_service():
    """
    Get EmailService instance.
    Creates a new instance each time to ensure tenant isolation.
    
    Returns:
        EmailService instance
    """
    return EmailService()