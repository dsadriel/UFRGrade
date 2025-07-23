# UFRGrade

Uma ferramenta Python para interagir com o sistema do portal UFRGS (Universidade Federal do Rio Grande do Sul). Este projeto fornece gerenciamento automatizado de sessão e utilitários para recuperar informações acadêmicas como matrícula em cursos, disciplinas elegíveis e turmas disponíveis.

## Requisitos

- Python 3.7+
- Pacotes necessários (instale via `pip install -r requirements.txt`):
  - `requests`
  - `beautifulsoup4`
  - `python-dotenv`
  - `rich`

## Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/dsadriel/UFRGrade.git
   cd UFRGrade
   ```

2. **Crie um ambiente virtual:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # No Windows: .venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente (opcional):**
   Crie um arquivo `.env` no diretório raiz:
   ```
   UFRGS_USERNAME=seu_usuario
   UFRGS_PASSWORD=sua_senha
   UFRGS_SEMESTER=2025/1
   UFRGS_TIME_FILTER=8:30|10:30
   ```

## Uso

### Uso Básico

Execute o script principal para obter disciplinas disponíveis para seu curso:

```bash
python main.py
```

O script irá:
1. Solicitar suas credenciais UFRGS (se não estiverem no `.env`)
2. Fazer login no portal UFRGS
3. Recuperar informações do seu curso
4. Encontrar disciplinas elegíveis
5. Filtrar turmas disponíveis por suas preferências de horário
6. Exibir os resultados

### Usando os Utilitários

```python
from UFRGSSession import create_session
from UFRGSUtils import UFRGSUtils

# Criar sessão
session = create_session("usuario", "senha")

# Inicializar utilitários
utils = UFRGSUtils(session)

# Obter informações do curso
course_name = utils.get_student_course_name()
course_code = utils.get_course_code(course_name)

# Obter disciplinas disponíveis
eligible = utils.get_eligible_disciplines()
available = utils.get_available_disciplines_for_semester_and_course("2025/1", course_code)
```

## Configuração

### Variáveis de Ambiente

- `UFRGS_USERNAME`: Seu nome de usuário do portal UFRGS
- `UFRGS_PASSWORD`: Sua senha do portal UFRGS
- `UFRGS_SEMESTER`: Semestre no formato AAAA/X (ex: "2025/1")
- `UFRGS_TIME_FILTER`: Padrão regex de filtro de horário (ex: "8:30|10:30" para aulas matutinas)

### Filtro de Horários

A aplicação permite filtrar turmas por horário. Você pode configurar isso de várias maneiras:

1. **Variável de Ambiente**: Defina `UFRGS_TIME_FILTER` no seu arquivo `.env`:
   ```
   # Aulas matutinas
   UFRGS_TIME_FILTER=8:30|10:30
   
   # Aulas vespertinas  
   UFRGS_TIME_FILTER=14:30|16:30
   
   # Horários específicos
   UFRGS_TIME_FILTER=8:30|14:30|19:00
   ```

2. **Entrada Interativa**: Se não definido no `.env`, o script solicitará que você digite seus horários preferidos.


## Licença

Este projeto está licenciado sob a Licença MIT. Isso significa que você pode usar, copiar, modificar e distribuir o software livremente, desde que mantenha o aviso de copyright e a licença. O software é fornecido "no estado em que se encontra" (as-is), sem garantias de qualquer tipo. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## Aviso Legal

Esta ferramenta é apenas para fins educacionais. Use com responsabilidade e de acordo com os termos de serviço da UFRGS. Os autores não são responsáveis por qualquer uso indevido deste software.

---

**Nota**: Este projeto não é oficialmente afiliado à UFRGS. É uma ferramenta independente criada para ajudar estudantes a interagir com o sistema do portal de forma mais eficiente.
