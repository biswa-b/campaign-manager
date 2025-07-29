from .email import EmailNotifier

# List of active notifiers that will be used to send notifications
# To add new notification types (SMS, webhook, etc.), import them here and add to this list
notifiers = [EmailNotifier()]

# Example of how to add more notifiers:
# from .sms import SMSNotifier
# from .webhook import WebhookNotifier
# notifiers = [EmailNotifier(), SMSNotifier(), WebhookNotifier()]
