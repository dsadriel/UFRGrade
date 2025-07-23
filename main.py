import re
from urllib import response
from UFRGSSession import create_or_load_session, UFRGSSession
import os
from getpass import getpass
from dotenv import load_dotenv
from UFRGSUtils import UFRGSUtils

def main():
    """
    Main function to demonstrate UFRGS portal login
    """
    print("UFRGS Portal Login")
    print("-" * 20)
    
    # Get credentials (you can also set these as environment variables)
    load_dotenv()
    username = os.getenv('UFRGS_USERNAME') or input("Enter your UFRGS username: ")
    password = os.getenv('UFRGS_PASSWORD') or getpass("Enter your UFRGS password: ")
    semester = os.getenv('UFRGS_SEMESTER') or input("Enter your UFRGS semester (YYYY/X): ")
    semester_code = UFRGSUtils.get_semester_code(semester)
    if not semester_code:
        print("❌ Invalid semester format. Please use YYYY/X format.")
        return

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
    
    ufrgs_utils = UFRGSUtils(ufrgs_session)


    course_name = ufrgs_utils.get_student_course_name()
    course_code = ufrgs_utils.get_course_code(course_name)
    if not course_name:
        print("❌ Failed to retrieve student course enrollment.")
        return

    print("Student Course Enrollment: ", course_name)
    print("Student Course Code: ", course_code)

    eligible_disciplines = ufrgs_utils.get_eligible_disciplines()
    available_disciplines = ufrgs_utils.get_available_disciplines_for_semester_and_course(semester, course_code)

    # Filter available disciplines for student, considering only those that are eligible
    available_disciplines_for_student = []
    for disc in available_disciplines:
        if any(disc["Sigla"] == eligible["Sigla"] for eligible in eligible_disciplines):
            available_disciplines_for_student.append(disc)


    # Remove classes that don't met the student's course requirements
    requirements_regex = r'(8:30|10:30)'

    filtered_disciplines = []
    for disc in available_disciplines_for_student:
        # Only keep classes that meet the requirement
        matching_classes = [
            class_option for class_option in disc["Turmas"]
            if any(re.search(requirements_regex, horario["Horário"]) for horario in class_option["Horários - Locais - Observações"])
        ]

        if matching_classes:
            # Copy the discipline and only include matching classes
            filtered_disc = disc.copy()
            filtered_disc["Turmas"] = matching_classes
            filtered_disciplines.append(filtered_disc)

    print(f"Available disciplines for {course_name} ({course_code}):")
    for disc in filtered_disciplines:
        print(f"--- {disc['Sigla']} ---")
        print(f"Nome        : {disc['Nome']}")
        for turma in disc["Turmas"]:
            print(f"Turma       : {turma.get('Turmas', 'N/A')}")
            print(f"Professor   : {turma.get('Professores', 'N/A')}")
            print(f"Horarios    : {turma.get('Horários - Locais - Observações', 'N/A')}")
            print("-" * 20)
        print("-" * 40)
    if not filtered_disciplines:
        print("No available disciplines found for the specified course and semester.")
        return

if __name__ == "__main__":
    main()

