#!/usr/bin/env python3
"""
Email Analysis Application - Main Entry Point
Integrates Gmail authentication, email fetching, database storage, and AI analysis
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.email.gmail_reader import GmailReader
from src.priotizer import prioritize_email
from src.logger import logger


def analyze_emails(reader: GmailReader, emails: List[Dict]):

    """Analyze and process fetched emails using a prioritizer """
    for email in emails:
        subject = email.get("subject", "No Subject")
        priority = prioritize_email(email)

        logger.info(f"Analyzing email ➜ Subject: {subject} | Priority: {priority}")

        ai_result = {
            "priority": priority,
            "summary": email.get("snippet", "")[:150]
        }

        reader.mark_email_processed(email["id"], ai_result)


def main():
    logger.info("📬 Starting Email Analysis App...")

    reader = GmailReader()

    try:
        
        emails = reader.fetch_and_store_recent_emails(max_results=5)
        logger.info(f"📨 Total emails fetched: {len(emails)}")

        if emails:
            analyze_emails(reader, emails)

            reader.display_recent_emails(limit=5)

            unprocessed = reader.get_unprocessed_emails()
            logger.info(f"🕵️ Unprocessed emails left: {len(unprocessed)}")

        else:
            logger.warning("📭 No new emails to process.")

    except Exception as e:
        logger.exception(f"❌ Error during execution: {e}")

    finally:
        reader.close_connections()
        logger.info("✅ App finished. Exiting...")


if __name__ == "__main__":
    main()

