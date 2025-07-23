# UFRGrade

A Python tool for interacting with the UFRGS (Universidade Federal do Rio Grande do Sul) portal system. This project provides automated session management and utilities for retrieving academic information such as course enrollment, eligible disciplines, and available classes.

## Requirements

- Python 3.7+
- Required packages (install via `pip install -r requirements.txt`):
  - `requests`
  - `beautifulsoup4`
  - `python-dotenv`
  - `rich`

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dsadriel/UFRGrade.git
   cd UFRGrade
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables (optional):**
   Create a `.env` file in the root directory:
   ```
   UFRGS_USERNAME=your_username
   UFRGS_PASSWORD=your_password
   UFRGS_SEMESTER=2025/1
   ```

## Usage

### Basic Usage

Run the main script to get available disciplines for your course:

```bash
python main.py
```

The script will:
1. Prompt for your UFRGS credentials (if not in `.env`)
2. Log into the UFRGS portal
3. Retrieve your course information
4. Find eligible disciplines
5. Filter available classes by your schedule preferences
6. Display the results

### Using the Session Manager

```python
from UFRGSSession import create_session, UFRGSLoginError

try:
    # Create a new session
    session = create_session("your_username", "your_password")
    
    # Make authenticated requests
    response = session.make_authenticated_request("https://www1.ufrgs.br/sistemas/portal/some_page")
    
    # Save session for later use
    session.save_session()
    
    # Check if session is still valid
    if session.is_session_valid():
        print("Session is active")
    
except UFRGSLoginError as e:
    print(f"Login failed: {e}")
```

### Using the Utilities

```python
from UFRGSSession import create_session
from UFRGSUtils import UFRGSUtils

# Create session
session = create_session("username", "password")

# Initialize utilities
utils = UFRGSUtils(session)

# Get course information
course_name = utils.get_student_course_name()
course_code = utils.get_course_code(course_name)

# Get available disciplines
eligible = utils.get_eligible_disciplines()
available = utils.get_available_disciplines_for_semester_and_course("2025/1", course_code)
```

## Project Structure

```
UFRGrade/
├── main.py              # Main application script
├── UFRGSSession.py      # Session management and authentication
├── UFRGSUtils.py        # Utility functions for UFRGS data
├── .env                 # Environment variables (create this)
├── .gitignore          # Git ignore file
└── README.md           # This file
```

## Core Components

### UFRGSSession

The `UFRGSSession` class provides:

- **Authentication**: Secure login to UFRGS portal
- **Session Management**: Save/load sessions to avoid repeated logins
- **Request Handling**: Make authenticated HTTP requests
- **Session Validation**: Check if current session is still active

### UFRGSUtils

The `UFRGSUtils` class provides:

- **Course Information**: Get student course enrollment details
- **Discipline Data**: Retrieve eligible and available disciplines
- **Schedule Filtering**: Filter classes by time and other criteria
- **Data Parsing**: Extract structured data from UFRGS portal pages

## Configuration

### Environment Variables

- `UFRGS_USERNAME`: Your UFRGS portal username
- `UFRGS_PASSWORD`: Your UFRGS portal password  
- `UFRGS_SEMESTER`: Semester in YYYY/X format (e.g., "2025/1")

### Schedule Filtering

The application includes example filtering for morning classes (8:30 and 10:30). You can modify the regex pattern in `main.py`:

```python
# Current filter for morning classes
hours_requirements_regex = r'(8:30|10:30)'

# Example: Filter for afternoon classes
hours_requirements_regex = r'(14:30|16:30)'
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational purposes only. Please use responsibly and in accordance with UFRGS terms of service. The authors are not responsible for any misuse of this software.

---

**Note**: This project is not officially affiliated with UFRGS. It's an independent tool created to help students interact with the portal system more efficiently.
