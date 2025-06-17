import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.email.gmail_reader import fetch_recent_mails

def main():
    print("Testing function.....")
    try:
        emails = fetch_recent_mails(max_results = 3)
        print(f"successfully fetched {len(emails)} mails")
        print("=" * 50)

        for i, email in enumerate(emails,1):
            print(f"\n Email{i}")
            print(f"subject : {email['subject']}")
            print(f"From : {email['sender']}")
            print(f"snippet : {email['snippet']}")
            print(f"body preview : {email['body_text'][:100]}.....")
            print("-" * 40)
    except Exception as e:
        print(f"error {e}")

if __name__ == "__main__":
    main()