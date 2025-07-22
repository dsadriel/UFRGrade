from urllib import response
from UFRGSSession import create_or_load_session, UFRGSSession
import os
from getpass import getpass

def main():
    """
    Main function to demonstrate UFRGS portal login
    """
    print("UFRGS Portal Login")
    print("-" * 20)
    
    # Get credentials (you can also set these as environment variables)
    username = os.getenv('UFRGS_USERNAME') or input("Enter your UFRGS username: ")
    password = os.getenv('UFRGS_PASSWORD') or getpass("Enter your UFRGS password: ")
    
    # Create and login to session
    ufrgs_session = None
    try:
        ufrgs_session = create_or_load_session(username, password)
        ufrgs_session.save_session()  # Save session for future use
    except Exception as e:
        print(f"Error creating session: {e}")
        return
    
    if not ufrgs_session:
        print("❌ Failed to create session. Please check your credentials.")
        return
    
    print("✅ Successfully logged in to UFRGS portal!")
    print("Testing session validation...")


    is_valid = ufrgs_session.is_session_valid()
    print(f"Session valid: {is_valid}")
   

if __name__ == "__main__":
    main()

