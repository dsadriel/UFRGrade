import logging
from bs4 import BeautifulSoup
from UFRGSSession import UFRGSSession
import re
from difflib import SequenceMatcher
import json

logger = logging.getLogger(__name__)

class UFRGSUtils:
    """
    Utility class for UFRGS portal operations.
    """

    def __init__(self, session: UFRGSSession):
        self.session = session.session

    def get_user_curriculum_analysis(self):
        """
        Function to get user curriculum analysis
        """

        response = self.session.get("https://www1.ufrgs.br/intranet/portal/public/index.php?cods=1,1,2,81")

        analysis = {}

        soup = BeautifulSoup(response.text, "html.parser")
        
        fieldsets = soup.select("fieldset.fieldset-2.moldura")

        for idx, fs in enumerate(fieldsets, 1):
            legend = fs.find("legend")
            if not legend:
                logger.info(f"Fieldset {idx} has no legend, skipping")
                continue

            legend = legend.text.strip()

            tableHeaders = [th.text.strip() for th in fs.select("table thead tr th")]
            
            if not tableHeaders:
                logger.warning(f"Fieldset {idx} has no table headers, skipping")
                continue

            tbody = fs.select_one("table tbody")
            if not tbody:
                logger.warning(f"Fieldset {idx} has no table body, skipping")
                continue
            tableRows = tbody.find_all("tr")

            if not tableRows:
                logger.warning(f"Fieldset {idx} has no table rows, skipping")
                continue
            
            for row in tableRows:
                cells = row.find_all("td")
                if len(cells) != len(tableHeaders):
                    continue
                
                rowData = {tableHeaders[i]: cells[i].text.strip() for i in range(len(tableHeaders))}

                if legend not in analysis:
                    analysis[legend] = []
                    
                analysis[legend].append(rowData)

        return analysis
    
    def get_student_course_name(self):
        """
        Function to get user course enrollment
        """
        response = self.session.get("https://www1.ufrgs.br/intranet/portal/public/index.php?cods=1,1,2,2")

        soup = BeautifulSoup(response.text, "html.parser")
        course_text = soup.select_one("fieldset.moldura")

        if not course_text:
            logger.warning("No course enrollment information found.")
            return None
        
        course_text = course_text.text.strip()
        match = re.search(r'Habilitação:\s*(.+)', course_text)
        if match:
            return match.group(1).strip()
        else:
            logger.warning("Could not parse course enrollment information.")
            return None

    def get_course_code(self, course_name=None):
        """
        Function to get course code from user course enrollment
        """
        if not course_name:
            course_name = self.get_user_course_name()
            if not course_name:
                logger.warning("No course enrollment information available.")
                return None
        
        response = self.session.get("https://www1.ufrgs.br/intranet/portal/public/index.php?cods=1,1,2,7")

        soup = BeautifulSoup(response.text, "html.parser")
        select = soup.find("select", id="selecionado")
        if not select:
            logger.warning("Could not find select#selecionado.")
            return None

        options = select.find_all("option")
        if not options:
            logger.warning("No options found in select#selecionado.")
            return None

        if not course_name:
            course_name = course_enrollment

        # Find the option most similar to course_name

        def similarity(a, b):
            return SequenceMatcher(None, a.lower(), b.lower()).ratio()

        best_option = max(options, key=lambda opt: similarity(opt.text.strip(), course_name))
        course_code = best_option.get("value")
        return course_code
    
    def get_eligible_disciplines(self):
        curriculum_analysis = self.get_user_curriculum_analysis()
        eligible_disciplines = []

        for key, value in curriculum_analysis.items():
            for discipline in value:
                # Skip disciplines that are not relevant 
                if discipline.get("Nome da Atividade").startswith("VÍNCULO ACADÊMICO"):
                    continue

                # Add discipline if it has the obtained prerequisite status
                if discipline.get("Situação") and discipline["Situação"] == "Pré-requisito(s) obtido(s)":
                    discipline["Etapa"] = key
                    if discipline not in eligible_disciplines:
                        eligible_disciplines.append(discipline)

        return eligible_disciplines
    
    @staticmethod
    def get_semester_code(semester: str) -> str:
        """
        Convert semester string to code.
        """

        matches = re.match(r"(^\d{4})/(\d)$", semester)

        if not matches:
            raise ValueError(f"Invalid semester format: {semester}. Expected format is YYYY/X.")

        year = matches.group(1)
        term = matches.group(2)

        return f"{year}0{term}2"

    def get_available_disciplines_for_semester_and_course(self, semester: str, course_code: str):
        """
        Get available disciplines for a specific semester and course.
        """
        semester_code = self.get_semester_code(semester)
        if not semester_code:
            logger.error(f"Invalid semester format: {semester}. Expected format is YYYY/X.")
            return []

        response = self.session.post(
            "https://www1.ufrgs.br/intranet/portal/public/index.php?cods=1,1,2,7",
            data={"PL": semester_code, "selecionado": course_code}
        )

        soup = BeautifulSoup(response.text, "html.parser")
        
        table = soup.select_one("table#Horarios")
        disciplines = []

        if not table:
            logger.warning("No table with id 'Horarios' found.")
            return disciplines

        rows = table.select("tr")
        if not rows:
            logger.warning("No rows found in table#Horarios.")
            return disciplines

        # Use the first tr in tbody as header
        header_cells = rows[0].find_all("th")
        headers = [cell.text.strip() for cell in header_cells]

        # Iterate over the remaining rows as data
        current_discipline = {}
        
        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) != len(headers):
             continue

            # If the cell is empty, indicates that is a class for the current discipline
            class_info = {}
        
            if cells[0].text.strip() != "": # Its a new discipline
                # Add the current discipline to the list if it has data
                if current_discipline.get("Sigla"):
                    disciplines.append(current_discipline)

                code, name = self.split_discipline_name(cells[0].text.strip())
                credits = cells[1].text.strip()
                plano = cells[10].find("a")["href"] if cells[10].find("a") else ""

                current_discipline = {
                    "Sigla": code,
                    "Nome": name,
                    "Créditos": credits,
                    "Plano de Ensino": plano,
                    "Turmas": []
                }
            
            for i, cell in enumerate(cells):
                if i == 0 or i == 1 or i == 10:
                    continue

                if headers[i] == "Horários - Locais - Observações":
                    # Special handling for Horários - Locais - Observações
                    # Parse the HTML inside the cell to extract schedule, location, and observations
                    horarios = []
                    locais = []

                    # Parse the cell HTML
                    cell_soup = BeautifulSoup(str(cell), "html.parser")
                    horarios_locais = []
                    for li in cell_soup.find_all("li", class_="hor"):
                        horario_text = li.text.strip()
                        local = ""
                        a = li.find("a", class_="clicavel")
                        if a:
                            local = a.text.strip()
                        horarios_locais.append({"Horário": horario_text, "Local": local})

                    class_info[headers[i]]= horarios_locais
                else:
                    class_info[headers[i]] = cell.text.strip()
            current_discipline["Turmas"].append(class_info)

        if len(disciplines) == 0:
            logger.warning("No disciplines found for the given semester and course.")
            return []
        
        return disciplines

    @staticmethod
    def split_discipline_name(discipline_name: str) -> tuple:
        """
        Split discipline name into code and name.
        """
        match = re.match(r"\(?([A-Z]{3}\d{5})\)\s+(.+)", discipline_name)
        if match:
            code = match.group(1).strip()
            name = match.group(2).strip()
            return code, name
        else:
            logger.warning(f"Could not parse discipline name: {discipline_name}")
            return None, discipline_name.strip()