from src.auth.gmail_auth import get_gmail_service

print("Testing Gmail authentication")
try:
    service = get_gmail_service()
    print("Authentication successful")
    profile = service.users().getProfile(userId = 'me').execute()
    print(f"Connected to : {profile['emailAddress']}")
    print(f"Total_messages : {profile['messagesTotal']}")
except Exception as e:
    print("Error : {e}")

   