import requests
import logging
import pickle
import os
import json
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UFRGSLoginError(Exception):
    """Exception raised when UFRGS login fails"""
    pass

class UFRGSSession:
    def __init__(self):
        self.session = requests.Session()
        self.login_url = "https://www1.ufrgs.br/sistemas/portal/login"
        
        # Set common headers to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def login(self, username, password):
        """
        Login to UFRGS portal with provided credentials
        
        Args:
            username (str): UFRGS username
            password (str): UFRGS password
            
        Returns:
            bool: True if login successful
            
        Raises:
            UFRGSLoginError: If login fails
            requests.exceptions.RequestException: For network-related errors
        """
        try:
            # Prepare login data with correct parameters from form analysis
            login_data = {
                'Destino': 'ccd7f388f9a3e25ef6aff3b98c773f65',
                'Origem': 'https%3A%2F%2Fwww.ufrgs.br%2F',  # URL encoded origin
                'Var1': '',
                'Var2': '',
                'usuario': username,
                'senha': password
            }
            
            logger.info(f"Attempting to login with username: {username}")
            
            # First, get the login page to establish session
            response = self.session.get(self.login_url)
            response.raise_for_status()
            
            # Post login credentials - DON'T follow redirects to check the response
            response = self.session.post(
                self.login_url,
                data=login_data,
                allow_redirects=False  # Important: Don't follow redirects
            )
            response.raise_for_status()
            
            # Check if login was successful
            if self._check_login_success(response):
                logger.info("Login successful!")
                return True
            else:
                logger.error("Login failed - invalid credentials or other error")
                raise UFRGSLoginError("Login failed - invalid credentials or authentication error")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during login: {e}")
            raise
        except UFRGSLoginError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            raise UFRGSLoginError(f"Unexpected error during login: {e}")
    
    def _check_login_success(self, response):
        """
        Check if login was successful by analyzing the response
        
        Args:
            response: Response object from login attempt
            
        Returns:
            bool: True if login appears successful
        """
        # UFRGS login success = HTTP 302 redirect to intranet portal
        if response.status_code == 302:
            location = response.headers.get('location', '')
            if 'intranet/portal/public/index.php' in location:
                logger.info(f"Login successful: redirected to {location}")
                return True
            else:
                logger.info(f"Login failed: unexpected redirect to {location}")
                return False
        
        # HTTP 200 means we stayed on login page = failure
        if response.status_code == 200:
            logger.info("Login failed: HTTP 200 response (stayed on login page)")
            return False
        
        # Any other status code is unexpected
        logger.warning(f"Unexpected login response status: {response.status_code}")
        return False
    
    def get_session_cookies(self):
        """
        Get current session cookies
        
        Returns:
            dict: Current session cookies
        """
        return dict(self.session.cookies)
    
    def make_authenticated_request(self, url, method='GET', **kwargs):
        """
        Make an authenticated request using the established session
        
        Args:
            url (str): URL to request
            method (str): HTTP method (GET, POST, etc.)
            **kwargs: Additional arguments for the request
            
        Returns:
            Response object
        """
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making authenticated request to {url}: {e}")
            raise
    
    def logout(self):
        """
        Logout from the portal (if logout endpoint is available)
        """
        try:
            # Common logout URLs for portal systems
            logout_url = "https://www1.ufrgs.br/portalservicos/sair.php"
            response = self.session.get(logout_url)
            
            if response.status_code == 200:
                logger.info("Logout successful")
            else:
                logger.warning(f"Logout failed: {response.status_code}")
            
            # Clear session
            self.session.cookies.clear()
            
        except Exception as e:
            logger.error(f"Error during logout: {e}")

    def save_session(self, session_file="ufrgs_session.pkl"):
        """
        Save the current session to a file
        
        Args:
            session_file (str): Path to save the session file
        """
        try:
            session_data = {
                'cookies': dict(self.session.cookies),
                'headers': dict(self.session.headers),
                'saved_at': datetime.now().isoformat()
            }
            
            with open(session_file, 'wb') as f:
                pickle.dump(session_data, f)
            
            logger.info(f"Session saved to {session_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            return False
    
    def load_session(self, session_file="ufrgs_session.pkl", max_age_hours=24):
        """
        Load a previously saved session from file
        
        Args:
            session_file (str): Path to the session file
            max_age_hours (int): Maximum age of session in hours before considering it expired
            
        Returns:
            bool: True if session loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(session_file):
                logger.info(f"Session file {session_file} not found")
                return False
            
            with open(session_file, 'rb') as f:
                session_data = pickle.load(f)
            
            # Check if session is too old
            saved_at = datetime.fromisoformat(session_data['saved_at'])
            if datetime.now() - saved_at > timedelta(hours=max_age_hours):
                logger.info(f"Session is older than {max_age_hours} hours, considering it expired")
                return False
            
            # Restore cookies and headers
            for name, value in session_data['cookies'].items():
                self.session.cookies.set(name, value)
            
            # Update headers (but keep the original ones as base)
            self.session.headers.update(session_data['headers'])
            
            logger.info(f"Session loaded from {session_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return False
    
    def is_session_valid(self, test_url=None):
        """
        Test if the current session is still valid by making a test request
        
        Args:
            test_url (str): URL to test the session against. If None, uses curriculum analysis URL
            
        Returns:
            bool: True if session is valid, False otherwise
        """
        try:
            if test_url is None:
                test_url = "https://www1.ufrgs.br/intranet/portal/public/index.php?cods=1,1,2,81"

            response = self.session.get(test_url, timeout=10, allow_redirects=True)

            # For protected pages: HTTP 200 = valid session, HTTP 302 = invalid session
            if response.status_code == 200:
                logger.info("Session is valid: got 200 response (authenticated access)")
                return True
            elif response.status_code == 302:
                location = response.headers.get('location', '')
                if 'teste_intranet.php' in location:
                    logger.info("Session invalid: redirected to authentication test")
                    return False
                elif 'login' in location.lower():
                    logger.info("Session invalid: redirected to login page")
                    return False
                else:
                    logger.info(f"Session invalid: unexpected redirect to {location}")
                    return False
            else:
                logger.info(f"Session status unclear: unexpected response code {response.status_code}")
                return False
            
        except Exception as e:
            logger.error(f"Error testing session validity: {e}")
            return False
    
    def save_session_json(self, session_file="ufrgs_session.json"):
        """
        Save session as JSON (alternative to pickle, more readable but less secure)
        
        Args:
            session_file (str): Path to save the session JSON file
        """
        try:
            session_data = {
                'cookies': dict(self.session.cookies),
                'headers': dict(self.session.headers),
                'saved_at': datetime.now().isoformat()
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.info(f"Session saved to {session_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session as JSON: {e}")
            return False
    
    def load_session_json(self, session_file="ufrgs_session.json", max_age_hours=24):
        """
        Load session from JSON file
        
        Args:
            session_file (str): Path to the session JSON file
            max_age_hours (int): Maximum age of session in hours
            
        Returns:
            bool: True if session loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(session_file):
                logger.info(f"Session file {session_file} not found")
                return False
            
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check if session is too old
            saved_at = datetime.fromisoformat(session_data['saved_at'])
            if datetime.now() - saved_at > timedelta(hours=max_age_hours):
                logger.info(f"Session is older than {max_age_hours} hours, considering it expired")
                return False
            
            # Restore cookies and headers
            for name, value in session_data['cookies'].items():
                self.session.cookies.set(name, value)
            
            self.session.headers.update(session_data['headers'])
            
            logger.info(f"Session loaded from {session_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading session from JSON: {e}")
            return False
    
    def delete_saved_session(self, session_file="ufrgs_session.pkl"):
        """
        Delete a saved session file
        
        Args:
            session_file (str): Path to the session file to delete
        """
        try:
            if os.path.exists(session_file):
                os.remove(session_file)
                logger.info(f"Session file {session_file} deleted")
                return True
            else:
                logger.info(f"Session file {session_file} not found")
                return False
        except Exception as e:
            logger.error(f"Error deleting session file: {e}")
            return False


def create_session(username, password):
    """
    Convenience function to create and login to UFRGS session
    
    Args:
        username (str): UFRGS username
        password (str): UFRGS password
        
    Returns:
        UFRGSSession: Logged-in session object
        
    Raises:
        UFRGSLoginError: If login fails
        requests.exceptions.RequestException: For network-related errors
    """
    session = UFRGSSession()
    session.login(username, password)  # Will raise exception if login fails
    return session


def create_or_load_session(username=None, password=None, session_file="ufrgs_session.pkl", max_age_hours=24):
    """
    Smart session creator that tries to load an existing session first, 
    and only logs in if no valid session exists
    
    Args:
        username (str): UFRGS username (required if no valid session exists)
        password (str): UFRGS password (required if no valid session exists)
        session_file (str): Path to the session file
        max_age_hours (int): Maximum age of session in hours
        
    Returns:
        UFRGSSession: Session object
        
    Raises:
        UFRGSLoginError: If login fails or no valid session and no credentials provided
        requests.exceptions.RequestException: For network-related errors
    """
    session = UFRGSSession()
    
    # Try to load existing session first
    if session.load_session(session_file, max_age_hours):
        logger.info("Loaded existing session")
        
        # Test if the loaded session is still valid
        if session.is_session_valid():
            logger.info("Loaded session is valid")
            return session
        else:
            logger.info("Loaded session is no longer valid, will need to login")
    
    # If no valid session exists, login with credentials
    if username and password:
        logger.info("Creating new session with login")
        session.login(username, password)  # Will raise exception if login fails
        # Save the new session for future use
        session.save_session(session_file)
        return session
    else:
        logger.error("No valid session found and no credentials provided")
        raise UFRGSLoginError("No valid session found and no credentials provided")


# Example usage
if __name__ == "__main__":
    # Example usage - replace with actual credentials
    username = "your_username"
    password = "your_password"
    
    try:
        # Create session
        ufrgs_session = create_session(username, password)
        
        print("Successfully logged in to UFRGS portal!")
        print("Session cookies:", ufrgs_session.get_session_cookies())
        
        # Example of making an authenticated request
        # response = ufrgs_session.make_authenticated_request("https://www1.ufrgs.br/sistemas/portal/some_page")
        
        # Logout when done
        ufrgs_session.logout()
        
    except UFRGSLoginError as e:
        print(f"Login failed: {e}")
    except Exception as e:
        print(f"Error: {e}")