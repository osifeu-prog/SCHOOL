# bot/utils.py
import logging

logger = logging.getLogger(__name__)

def format_user_name(user):
    """פורמט את שם המשתמש להצגה"""
    if user.first_name:
        return user.first_name
    elif user.username:
        return user.username
    else:
        return f"User {user.id}"
