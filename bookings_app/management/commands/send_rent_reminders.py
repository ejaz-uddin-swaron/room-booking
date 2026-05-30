import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from bookings_app.models import RentSchedule

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sends email reminders for upcoming or overdue rent payments.'

    def handle(self, *args, **options):
        today = timezone.now().date()
        schedules = RentSchedule.objects.filter(status='active').prefetch_related('payment_history')
        
        emails_sent = 0

        for schedule in schedules:
            # Calculate due date for the current month
            last_day = (timezone.datetime(today.year, today.month, 28) + timezone.timedelta(days=4)).replace(day=1) - timezone.timedelta(days=1)
            safe_due_day = min(schedule.due_day, last_day.day)
            due_date = timezone.datetime(today.year, today.month, safe_due_day).date()
            days_until_due = (due_date - today).days

            # Determine if we should send a reminder today
            # We send on exactly 5 days before, 1 day before, and 1 day overdue
            if days_until_due not in [5, 1, -1]:
                continue

            current_month = today.strftime('%Y-%m')
            payment_exists = any(
                p.due_date.strftime('%Y-%m') == current_month and p.status == 'paid'
                for p in schedule.payment_history.all()
            )

            if payment_exists:
                continue

            # Identify the recipient
            recipient_email = schedule.tenant_email
            if schedule.tenant_user and schedule.tenant_user.email:
                recipient_email = schedule.tenant_user.email

            if not recipient_email:
                self.stdout.write(self.style.WARNING(f"Skipping schedule {schedule.id}: No email address found."))
                continue

            # Prepare the email
            status_text = "OVERDUE" if days_until_due < 0 else "UPCOMING"
            subject = f"[{status_text}] Rent Reminder: {schedule.room_name}"
            
            if days_until_due < 0:
                body = (
                    f"Dear {schedule.tenant_name},\n\n"
                    f"This is a reminder that your rent for {schedule.room_name} was due on {due_date.strftime('%B %d, %Y')}.\n"
                    f"Amount Due: ${schedule.monthly_rent}\n\n"
                    f"Please log in to your tenant dashboard to review your schedule or contact management immediately.\n\n"
                    f"Thank you,\nNeoScape Properties Management"
                )
            else:
                body = (
                    f"Dear {schedule.tenant_name},\n\n"
                    f"This is a friendly reminder that your rent for {schedule.room_name} is due on {due_date.strftime('%B %d, %Y')}.\n"
                    f"Amount Due: ${schedule.monthly_rent}\n\n"
                    f"Please log in to your tenant dashboard to review your schedule.\n\n"
                    f"Thank you,\nNeoScape Properties Management"
                )

            try:
                send_mail(
                    subject,
                    body,
                    settings.EMAIL_HOST_USER or 'noreply@neoscape.com',
                    [recipient_email],
                    fail_silently=False,
                )
                emails_sent += 1
                self.stdout.write(self.style.SUCCESS(f"Sent reminder for {schedule.room_name} to {recipient_email}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to send email to {recipient_email}: {str(e)}"))
                logger.error(f"Rent reminder email failed for {schedule.id}: {str(e)}")

        self.stdout.write(self.style.SUCCESS(f'Finished sending {emails_sent} rent reminder emails.'))
