#!/usr/bin/env python3
"""
Email Analysis Application - Main Entry Point
Integrates Gmail authentication, email fetching, parsing, AI analysis, and prioritization
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Clean and reliable imports
from src.auth.gmail_auth import authenticate_gmail
from src.email.gmail_reader import GmailReader
from src.database.email_db import EmailDatabase
from src.ai_analyzer import AIAnalyzer
from src.utils.email_parser import EmailParser
from src.utils.prioritizer import Prioritizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class EmailAnalysisApp:
    def __init__(self):
        self.service = None
        self.gmail_reader = None
        self.database = None
        self.ai_analyzer = None
        self.parser = None
        self.prioritizer = None

    def initialize(self) -> bool:
        try:
            logger.info("Initializing Email Analysis Application...")

            self.service = authenticate_gmail()
            if not self.service:
                logger.error("Failed to authenticate with Gmail - service is None")
                return False

            self.gmail_reader = GmailReader(self.service)
            self.database = EmailDatabase()
            self.ai_analyzer = AIAnalyzer()
            self.parser = EmailParser()
            self.prioritizer = Prioritizer()

            logger.info("Application initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            return False

    def fetch_parse_analyze_and_prioritize(self, query: str = "is:unread", max_results: int = 50) -> Dict[str, Any]:
        try:
            logger.info(f"Fetching emails with query: {query}")
            emails = self.gmail_reader.get_emails(query=query, max_results=max_results)
            if not emails:
                return {"status": "success", "emails_processed": 0, "analysis": None}

            analyzed_emails = []
            for email in emails:
                try:
                    parsed_email = self.parser.parse(email)
                    email_id = self.database.store_email(parsed_email)
                    if email_id:
                        analysis = self.ai_analyzer.analyze_email(parsed_email)
                        priority = self.prioritizer.get_priority(analysis)
                        if analysis:
                            self.database.store_analysis(email_id, analysis, priority)
                            analyzed_emails.append({
                                "email_id": email_id,
                                "subject": parsed_email.get("subject", "No Subject"),
                                "sender": parsed_email.get("sender", "Unknown"),
                                "priority": priority,
                                "analysis": analysis
                            })
                except Exception as e:
                    logger.error(f"Error processing email: {str(e)}")
                    continue

            return {
                "status": "success",
                "emails_processed": len(emails),
                "emails_analyzed": len(analyzed_emails),
                "analysis": analyzed_emails
            }
        except Exception as e:
            logger.error(f"Error during processing: {str(e)}")
            return {"status": "error", "message": str(e)}

    def get_analysis_summary(self, days_back: int = 7) -> Dict[str, Any]:
        try:
            since_date = datetime.now() - timedelta(days=days_back)
            summary = self.database.get_analysis_summary(since_date)
            return {"status": "success", "summary": summary, "period": f"Last {days_back} days"}
        except Exception as e:
            logger.error(f"Error getting summary: {str(e)}")
            return {"status": "error", "message": str(e)}

    def search_emails(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            return self.database.search_emails(search_term, limit)
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []

    def run_interactive_mode(self):
        print("\nWelcome to Email Analysis Application")
        while True:
            print("\n1. Fetch, parse, analyze and prioritize emails")
            print("2. View analysis summary")
            print("3. Search emails")
            print("4. Exit")
            choice = input("Enter choice: ").strip()

            if choice == "1":
                query = input("Query (default: is:unread): ") or "is:unread"
                max_results = input("Max results (default: 50): ")
                max_results = int(max_results) if max_results.isdigit() else 50
                result = self.fetch_parse_analyze_and_prioritize(query, max_results)
                print(result)

            elif choice == "2":
                days = input("Days to summarize (default: 7): ")
                days = int(days) if days.isdigit() else 7
                summary = self.get_analysis_summary(days)
                print(summary)

            elif choice == "3":
                term = input("Search term: ").strip()
                results = self.search_emails(term)
                for i, email in enumerate(results, 1):
                    print(f"{i}. {email.get('subject')} from {email.get('sender')}")

            elif choice == "4":
                print("Exiting.")
                break
            else:
                print("Invalid option")

def main():
    print("Starting Email Analysis Application...")
    app = EmailAnalysisApp()
    if not app.initialize():
        print("Failed to initialize. Check logs.")
        sys.exit(1)

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "--fetch":
            query = sys.argv[2] if len(sys.argv) > 2 else "is:unread"
            max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 50
            result = app.fetch_parse_analyze_and_prioritize(query, max_results)
            print(result)

        elif command == "--summary":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            summary = app.get_analysis_summary(days)
            print(summary)

        elif command == "--search":
            term = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
            results = app.search_emails(term)
            for email in results:
                print(f"{email.get('subject')} from {email.get('sender')}")

        else:
            print("Unknown command. Try --fetch, --summary, or --search")
    else:
        app.run_interactive_mode()

if __name__ == "__main__":
    main()
