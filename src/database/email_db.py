import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional


class EmailDatabase:
    """Simple file-based database for email storage"""

    def __init__(self, db_file: str = "emails.json"):
        """Initialize file-based database"""
        self.db_file = db_file
        self.emails = self._load_database()

    def _load_database(self) -> List[Dict]:
        """Load emails from JSON file"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"✅ Loaded {len(data)} emails from database")
                    return data
            except Exception as e:
                print(f"⚠️ Error loading database: {e}")
                return []
        else:
            print("📁 Creating new database file")
            return []

    def _save_database(self):
        """Save emails to JSON file"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.emails, f, indent=2, default=str)
        except Exception as e:
            print(f"❌ Error saving database: {e}")

    def store_email(self, email_data: Dict) -> str:
        """Store email in database"""
        try:
            existing_email = next((email for email in self.emails if email['id'] == email_data['id']), None)
            if existing_email:
                print(f"📧 Email {email_data['id']} already exists in database")
                return existing_email.get('db_id', str(uuid.uuid4()))

            db_id = str(uuid.uuid4())
            email_data['db_id'] = db_id
            email_data['created_at'] = datetime.utcnow().isoformat()
            email_data['processed'] = False
            email_data['ai_analysis'] = None

            self.emails.append(email_data)
            self._save_database()

            print(f"💾 Stored email: {email_data.get('subject', 'No Subject')}")
            return db_id
        except Exception as e:
            print(f"❌ Error storing email: {e}")
            return None

    def get_unprocessed_emails(self, limit: int = 10) -> List[Dict]:
        """Get emails that haven't been processed by AI"""
        try:
            unprocessed = [email for email in self.emails if not email.get('processed', False)]
            unprocessed.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return unprocessed[:limit]
        except Exception as e:
            print(f"❌ Error getting unprocessed emails: {e}")
            return []

    def get_recent_emails(self, limit: int = 5) -> List[Dict]:
        """Get most recent emails"""
        try:
            sorted_emails = sorted(self.emails, key=lambda x: x.get('created_at', ''), reverse=True)
            return sorted_emails[:limit]
        except Exception as e:
            print(f"❌ Error getting recent emails: {e}")
            return []

    def mark_email_processed(self, email_id: str, ai_analysis: Dict) -> bool:
        """Mark an email as processed with AI analysis results"""
        try:
            for email in self.emails:
                if email['id'] == email_id:
                    email['processed'] = True
                    email['ai_analysis'] = ai_analysis
                    email['processed_at'] = datetime.utcnow().isoformat()
                    self._save_database()
                    print(f"✅ Marked email {email_id} as processed")
                    return True
            print(f"⚠️ No email found with ID {email_id}")
            return False
        except Exception as e:
            print(f"❌ Error marking email as processed: {e}")
            return False

    def get_conversation_history(self, thread_id: str) -> List[Dict]:
        """Get all emails in a conversation thread"""
        try:
            thread_emails = [email for email in self.emails if email.get('thread_id') == thread_id]
            thread_emails.sort(key=lambda x: x.get('created_at', ''))
            return thread_emails
        except Exception as e:
            print(f"❌ Error getting conversation history: {e}")
            return []

    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            total_emails = len(self.emails)
            processed_emails = len([email for email in self.emails if email.get('processed', False)])
            unprocessed_emails = total_emails - processed_emails
            unique_senders = len(set(email.get('sender_email', '') for email in self.emails if email.get('sender_email')))

            dates = sorted(email.get('created_at', '') for email in self.emails if email.get('created_at'))
            oldest_date = dates[0] if dates else "N/A"
            newest_date = dates[-1] if dates else "N/A"

            return {
                "total_emails": total_emails,
                "processed_emails": processed_emails,
                "unprocessed_emails": unprocessed_emails,
                "unique_senders": unique_senders,
                "oldest_email_date": oldest_date,
                "newest_email_date": newest_date
            }
        except Exception as e:
            print(f"❌ Error getting database stats: {e}")
            return {}

    def close_connection(self):
        """Close the database connection (save final state)"""
        self._save_database()
        print("💾 Database saved and closed")


# Optional test
if __name__ == "__main__":
    try:
        db = EmailDatabase()
        stats = db.get_database_stats()
        print("\n📊 Database Statistics:")
        for key, value in stats.items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
        db.close_connection()
    except Exception as e:
        print(f"❌ Error testing database: {e}")
