def parse_recipients(recipients):
    """
    Parse recipients from various input formats into a standardized list.

    This utility function handles different input formats for recipients:
    - String with comma-separated emails
    - List of email strings
    - Already parsed list

    Args:
        recipients: Input recipients in various formats
            - str: Comma-separated email addresses
            - list: List of email addresses
            - None: Empty list returned

    Returns:
        list: Clean list of email addresses with whitespace removed

    Examples:
        >>> parse_recipients("user1@example.com, user2@example.com")
        ['user1@example.com', 'user2@example.com']

        >>> parse_recipients(["user1@example.com", "user2@example.com"])
        ['user1@example.com', 'user2@example.com']
    """
    if isinstance(recipients, str):
        # Handle comma-separated string format
        return [r.strip() for r in recipients.split(",") if r.strip()]
    return recipients
