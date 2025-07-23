import re
from urllib import response
from UFRGSSession import create_or_load_session, UFRGSSession
import os
from getpass import getpass
from dotenv import load_dotenv
from UFRGSUtils import UFRGSUtils
from rich.console import Console
from rich.table import Table

def main():
    """
    Main function to demonstrate UFRGS portal login
    """
    print("Filtro e Validação de Disciplinas UFRGS")
    print("-" * 40)
    
    # Get credentials (you can also set these as environment variables)
    load_dotenv()
    username = os.getenv('UFRGS_USERNAME') or input("Digite seu usuário UFRGS: ")
    password = os.getenv('UFRGS_PASSWORD') or getpass("Digite sua senha UFRGS: ")
    semester = os.getenv('UFRGS_SEMESTER') or input("Digite o semestre UFRGS (AAAA/X): ")
    time_filter = os.getenv('UFRGS_TIME_FILTER') or input("Digite o filtro de horário (ex: '8:30|10:30' para aulas matutinas): ")
    
    semester_code = UFRGSUtils.get_semester_code(semester)
    if not semester_code:
        print("❌ Formato de semestre inválido. Use o formato AAAA/X.")
        return

    # Create and login to session
    ufrgs_session = None
    try:
        ufrgs_session = create_or_load_session(username, password)
        ufrgs_session.save_session()  # Save session for future use
    except Exception as e:
        print(f"Erro ao criar sessão: {e}")
        return
    
    if not ufrgs_session:
        print("❌ Falhou ao criar sessão. Verifique suas credenciais.")
        return
    
    print("✅ Login realizado com sucesso no portal UFRGS!")
    
    ufrgs_utils = UFRGSUtils(ufrgs_session)


    course_name = ufrgs_utils.get_student_course_name()
    course_code = ufrgs_utils.get_course_code(course_name)
    if not course_name:
        print("❌ Falhou ao recuperar matrícula do curso do estudante.")
        return

    print("Matrícula do Curso do Estudante: ", course_name)
    print("Código do Curso do Estudante: ", course_code)

    eligible_disciplines = ufrgs_utils.get_eligible_disciplines()
    available_disciplines = ufrgs_utils.get_available_disciplines_for_semester_and_course(semester, course_code)

    # Filter available disciplines for student, considering only those that are eligible
    available_disciplines_for_student = []
    for disc in available_disciplines:
        if any(disc["Sigla"] == eligible["Sigla"] for eligible in eligible_disciplines):
            available_disciplines_for_student.append(disc)


    # Remove classes that don't meet the student's time preferences
    if time_filter:
        hours_requirements_regex = rf'({time_filter})'
        print(f"📅 Filtrando aulas para horários: {time_filter}")
    else:
        hours_requirements_regex = None
        print("📅 Nenhum filtro de horário aplicado - mostrando todos os horários disponíveis")

    filtered_disciplines = []
    for disc in available_disciplines_for_student:
        if hours_requirements_regex:
            # Only keep classes that meet the time requirement
            matching_classes = [
                class_option for class_option in disc["Turmas"]
                if all(re.search(hours_requirements_regex, horario["Horário"]) for horario in class_option["Horários - Locais - Observações"])
            ]
        else:
            # No time filter - include all classes
            matching_classes = disc["Turmas"]

        if matching_classes:
            # Copy the discipline and only include matching classes
            filtered_disc = disc.copy()
            filtered_disc["Turmas"] = matching_classes
            filtered_disciplines.append(filtered_disc)

    print(f"Disciplinas disponíveis para {course_name} ({course_code}):")
    for disc in filtered_disciplines:
        console = Console()
        table = Table(title=f"{disc['Sigla']} - {disc['Nome']}", show_lines=True)

        table.add_column("Turma", style="cyan", no_wrap=True)
        table.add_column("Professores", style="magenta")
        table.add_column("Horários", style="green")

        for turma in disc["Turmas"]:
            turma_id = turma.get('Turmas', 'N/A')
            professores = ', '.join(turma.get('Professores', ['N/A']))
            horarios = "\n".join(
                f"{h.get('Horário', 'N/A')} - {h.get('Local', 'N/A')}"
                for h in turma.get('Horários - Locais - Observações', [])
            )
            table.add_row(str(turma_id), professores, horarios)

        console.print(table)
        print("\n"*2)
    if not filtered_disciplines:
        print("Nenhuma disciplina disponível encontrada para o curso e semestre especificados.")
        return

if __name__ == "__main__":
    main()

