class Notifier:
    """
    Base class for all notification types.

    This abstract base class defines the interface that all notification
    implementations must follow. It provides a consistent interface for
    sending notifications regardless of the underlying technology (email, SMS, etc.).

    Subclasses should implement the send method to handle specific notification types.
    """

    def send(self, title: str, message: str, recipients: list[str]):
        """
        Send a notification to the specified recipients.

        This method must be implemented by subclasses to handle the actual
        sending of notifications through their respective channels.

        Args:
            title (str): The title/subject of the notification
            message (str): The main content of the notification
            recipients (list[str]): List of recipient addresses (emails, phone numbers, etc.)

        Raises:
            NotImplementedError: If the subclass doesn't implement this method
        """
        raise NotImplementedError
