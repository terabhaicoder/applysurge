"""
JobPilot email module.

Handles email sending via SendGrid, open/click tracking,
and incoming email parsing.
"""

from worker.email.email_sender import EmailSender
from worker.email.email_tracker import EmailTracker
from worker.email.email_parser import EmailParser

__all__ = [
    "EmailSender",
    "EmailTracker",
    "EmailParser",
]
