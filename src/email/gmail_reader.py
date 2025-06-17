import base64
import re
from typing import Dict, List, Optional
from src.auth.gmail_auth import get_gmail_service
from src.database.email_db import EmailDatabase


class GmailReader:
    """Enhanced Gmail reader with database integration"""
    
    def __init__(self):
        self.service = None
        self.db = None
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize Gmail and Database connections"""
        try:
            self.service = get_gmail_service()
            self.db = EmailDatabase()
            print("✅ Gmail and Database connections initialized")
        except Exception as e:
            print(f"❌ Error initializing connections: {e}")
            raise
    
    def fetch_and_store_recent_emails(self, max_results: int = 10, store_in_db: bool = True) -> List[Dict]:
        """
        Fetch recent emails and optionally store them in database
        
        Args:
            max_results: Maximum number of emails to fetch
            store_in_db: Whether to store emails in MongoDB
            
        Returns:
            List of processed email dictionaries
        """
        print(f"🔍 Fetching {max_results} recent emails...")
        
        try:
            # Get email list from Gmail
            results = self.service.users().messages().list(
                userId="me",
                labelIds=['INBOX'],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print("📭 No messages found")
                return []
            
            print(f"📬 Found {len(messages)} messages. Processing...")
            
            processed_emails = []
            for i, message in enumerate(messages, 1):
                print(f"📧 Processing email {i}/{len(messages)}...")
                
                try:
                    # Fetch email details
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=message['id']
                    ).execute()
                    
                    # Process email data
                    email_data = self._process_message(msg)
                    
                    # Store in database if requested
                    if store_in_db and self.db:
                        db_id = self.db.store_email(email_data)
                        email_data['db_id'] = db_id
                    
                    processed_emails.append(email_data)
                    
                except Exception as e:
                    print(f"⚠️ Error processing email {i}: {e}")
                    continue
            
            print(f"✅ Successfully processed {len(processed_emails)} emails")
            
            if store_in_db and self.db:
                self._print_database_stats()
            
            return processed_emails
            
        except Exception as e:
            print(f"❌ Error in fetch_and_store_recent_emails: {e}")
            return []
    
    def _process_message(self, msg: Dict) -> Dict:
        """Extract and structure email information"""
        
        headers = msg['payload'].get('headers', [])
        
        # Initialize email data structure
        email_data = {
            'id': msg['id'],
            'thread_id': msg['threadId'],
            'snippet': msg.get('snippet', ''),
            'subject': '',
            'sender': '',
            'sender_email': '',
            'sender_name': '',
            'recipient': '',
            'date': '',
            'body_text': '',
            'body_html': '',
            'labels': msg.get('labelIds', []),
            'attachments': [],
            'message_size': msg.get('sizeEstimate', 0)
        }
        
        # Extract header information
        for header in headers:
            name = header['name'].lower()
            value = header['value']
            
            if name == 'subject':
                email_data['subject'] = value
            elif name == 'from':
                email_data['sender'] = value
                email_data['sender_email'] = self._extract_email_address(value)
                email_data['sender_name'] = self._extract_sender_name(value)
            elif name == 'to':
                email_data['recipient'] = value
            elif name == 'date':
                email_data['date'] = value
        
        # Extract email body content
        body_data = self._extract_body(msg['payload'])
        email_data['body_text'] = body_data.get('text', '')
        email_data['body_html'] = body_data.get('html', '')
        
        # Extract attachment information
        email_data['attachments'] = self._extract_attachments(msg['payload'])
        
        return email_data
    
    def _extract_body(self, payload: Dict) -> Dict:
        """Extract both text and HTML body from email payload"""
        body_data = {'text': '', 'html': ''}
        
        try:
            if 'parts' in payload:
                # Multi-part message
                body_data = self._extract_from_parts(payload['parts'])
            elif payload.get('body', {}).get('data'):
                # Simple message
                mime_type = payload.get('mimeType', '')
                decoded_body = base64.urlsafe_b64decode(
                    payload['body']['data']
                ).decode('utf-8')
                
                if mime_type == 'text/plain':
                    body_data['text'] = decoded_body
                elif mime_type == 'text/html':
                    body_data['html'] = decoded_body
                    
        except Exception as e:
            print(f"⚠️ Error extracting body: {e}")
        
        return body_data
    
    def _extract_from_parts(self, parts: List[Dict]) -> Dict:
        """Recursively extract text and HTML from email parts"""
        body_data = {'text': '', 'html': ''}
        
        for part in parts:
            if 'parts' in part:
                # Nested parts
                nested_body = self._extract_from_parts(part['parts'])
                if not body_data['text'] and nested_body['text']:
                    body_data['text'] = nested_body['text']
                if not body_data['html'] and nested_body['html']:
                    body_data['html'] = nested_body['html']
                    
            elif part.get('body', {}).get('data'):
                try:
                    decoded_text = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8')
                    
                    mime_type = part.get('mimeType', '')
                    if mime_type == 'text/plain' and not body_data['text']:
                        body_data['text'] = decoded_text
                    elif mime_type == 'text/html' and not body_data['html']:
                        body_data['html'] = decoded_text
                        
                except Exception as e:
                    print(f"⚠️ Error decoding part: {e}")
                    continue
        
        return body_data
    
    def _extract_attachments(self, payload: Dict) -> List[Dict]:
        """Extract attachment information from email payload"""
        attachments = []
        
        def process_parts(parts):
            for part in parts:
                if 'parts' in part:
                    process_parts(part['parts'])
                else:
                    filename = part.get('filename', '')
                    if filename:
                        attachment_info = {
                            'filename': filename,
                            'mime_type': part.get('mimeType', ''),
                            'size': part.get('body', {}).get('size', 0),
                            'attachment_id': part.get('body', {}).get('attachmentId', '')
                        }
                        attachments.append(attachment_info)
        
        if 'parts' in payload:
            process_parts(payload['parts'])
        
        return attachments
    
    def _extract_email_address(self, sender_string: str) -> str:
        """Extract email address from sender string"""
        if not sender_string:
            return ""
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, sender_string)
        return match.group() if match else sender_string
    
    def _extract_sender_name(self, sender_string: str) -> str:
        """Extract sender name from sender string"""
        if not sender_string:
            return ""
        
        # Format: "Name <email@domain.com>"
        if '<' in sender_string:
            return sender_string.split('<')[0].strip().strip('"')
        
        # Just an email address
        if '@' in sender_string:
            return sender_string.split('@')[0]
        
        return sender_string
    
    def get_unprocessed_emails(self, limit: int = 10) -> List[Dict]:
        """Get emails from database that haven't been processed by AI"""
        if not self.db:
            print("❌ Database not connected")
            return []
        
        return self.db.get_unprocessed_emails(limit)
    
    def mark_email_processed(self, email_id: str, ai_analysis: Dict) -> bool:
        """Mark an email as processed with AI analysis results"""
        if not self.db:
            print("❌ Database not connected")
            return False
        
        return self.db.mark_email_processed(email_id, ai_analysis)
    
    def get_conversation_history(self, thread_id: str) -> List[Dict]:
        """Get all emails in a conversation thread"""
        if not self.db:
            print("❌ Database not connected")
            return []
        
        return self.db.get_conversation_history(thread_id)
    
    def _print_database_stats(self):
        """Print current database statistics"""
        if not self.db:
            return
        
        stats = self.db.get_database_stats()
        print("\n📊 Database Statistics:")
        for key, value in stats.items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
    
    def display_recent_emails(self, limit: int = 5):
        """Display recent emails from database"""
        if not self.db:
            print("❌ Database not connected")
            return
        
        try:
            emails = list(self.db.emails.find().sort("created_at", -1).limit(limit))
            
            print(f"\n📧 {len(emails)} Most Recent Emails:")
            print("=" * 80)
            
            for i, email in enumerate(emails, 1):
                print(f"\n{i}. 📬 {email.get('subject', 'No Subject')}")
                print(f"   👤 From: {email.get('sender_name', 'Unknown')} <{email.get('sender_email', '')}>")
                print(f"   📅 Date: {email.get('date', 'Unknown')}")
                print(f"   🔄 Processed: {' Yes' if email.get('processed') else '❌ No'}")
                
                # Show body preview
                body_text = email.get('body_text', '')
                if body_text:
                    preview = body_text.replace('\n', ' ').strip()[:150]
                    print(f"   📝 Preview: {preview}{'...' if len(preview) >= 150 else ''}")
                
                # Show attachments if any
                attachments = email.get('attachments', [])
                if attachments:
                    print(f"   📎 Attachments: {len(attachments)} file(s)")
                    
        except Exception as e:
            print(f" Error displaying emails: {e}")
    
    def close_connections(self):
        """Close database connection"""
        if self.db:
            self.db.close_connection()
            print(" Database connection closed")


# Convenience functions for backward compatibility
def fetch_recent_mails(max_results=5):
    """Legacy function - use GmailReader class instead"""
    reader = GmailReader()
    try:
        return reader.fetch_and_store_recent_emails(max_results)
    finally:
        reader.close_connections()


if __name__ == "__main__":
    # Test the enhanced Gmail reader
    reader = GmailReader()
    
    try:
        # Fetch and store emails
        emails = reader.fetch_and_store_recent_emails(max_results=5)
        
        if emails:
            print(f"\n Successfully processed {len(emails)} emails")
            
            # Display stored emails
            reader.display_recent_emails()
            
            # Show unprocessed emails count
            unprocessed = reader.get_unprocessed_emails()
            print(f"\n Unprocessed emails ready for AI analysis: {len(unprocessed)}")
        else:
            print("No emails were processed")
            
    except Exception as e:
        print(f" Error: {e}")
        
    finally:
        reader.close_connections()
        print("\n Process completed!")

