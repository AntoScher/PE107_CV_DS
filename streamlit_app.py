import os
import re
import streamlit as st
from deepseek_api import DeepSeekAPI, DeepSeekAPIError
from parse_hh import get_html, extract_vacancy_data, extract_resume_data, ParseError
from urllib.parse import urlparse

# Constants
SYSTEM_PROMPT = """
Проскорь кандидата, насколько он подходит для данной вакансии.

Сначала напиши короткий анализ, который будет пояснять оценку.
Отдельно оцени качество заполнения резюме (понятно ли, с какими задачами сталкивался кандидат и каким образом их решал?).
Эта оценка должна учитываться при выставлении финальной оценки - нам важно нанимать таких кандидатов, которые могут рассказать про свою работу.
Потом представь результат в виде оценки от 1 до 10.
""".strip()

# Configuration
CONFIG = {
    'required_fields': ['job_url', 'cv_url'],
    'max_retries': 3,
    'request_timeout': 30
}

# Initialize session state
if 'api_initialized' not in st.session_state:
    st.session_state.api_initialized = False

def validate_url(url: str, domain: str = 'hh.ru') -> bool:
    """Validate if URL is from the specified domain."""
    if not url:
        return False
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], 
                   result.netloc.endswith(domain)])
    except ValueError:
        return False

def initialize_api():
    """Initialize the DeepSeek API client."""
    try:
        api_key = st.secrets.get("DEEPSEEK_API_KEY")
        if not api_key:
            st.error("⚠️ API ключ не найден. Пожалуйста, укажите ваш DeepSeek API ключ в файле .streamlit/secrets.toml")
            st.code("""[DEEPSEEK_API_KEY] = "ваш_ключ_здесь""", language='toml')
            st.stop()
        
        client = DeepSeekAPI(api_key=api_key)
        st.session_state.client = client
        st.session_state.api_initialized = True
        return client
    except Exception as e:
        st.error(f"Ошибка при инициализации API: {str(e)}")
        st.stop()

def request_deepseek(system_prompt: str, user_prompt: str) -> str:
    """Send a request to the DeepSeek API with error handling and retries."""
    if not st.session_state.api_initialized:
        client = initialize_api()
    else:
        client = st.session_state.client
    
    try:
        response = client.chat(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0,
        )
        
        # Debug: Print the full response structure
        print("API Response:", response)  # This will be visible in the terminal
        
        # Handle different response formats
        if isinstance(response, dict):
            if 'choices' in response and len(response['choices']) > 0:
                return response['choices'][0].get('message', {}).get('content', 'No content')
            elif 'text' in response:
                return response['text']
            else:
                return str(response)  # Fallback to string representation
        
        # If response is not a dictionary, try to get its string representation
        return str(response)
        
    except DeepSeekAPIError as e:
        st.error(f"Ошибка API DeepSeek: {str(e)}")
        st.error("Пожалуйста, проверьте ваш API ключ и повторите попытку.")
    except Exception as e:
        st.error(f"Произошла непредвиденная ошибка: {str(e)}")
        st.exception(e)  # This will show the full traceback in the terminal
    return "Не удалось получить ответ от API. Пожалуйста, проверьте логи для подробностей."

def main():
    """Main application function."""
    st.title('📊 Анализ соответствия резюме и вакансии')
    st.markdown("---")
    
    # Initialize API
    if not st.session_state.api_initialized:
        initialize_api()
    
    # Input fields
    job_url = st.text_input('🔗 Ссылка на вакансию (hh.ru)', 
                          placeholder='https://hh.ru/vacancy/...')
    cv_url = st.text_input('📄 Ссылка на резюме (hh.ru)',
                         placeholder='https://hh.ru/resume/...')
    
    # Validate URLs
    if not validate_url(job_url) and job_url:
        st.warning("Пожалуйста, укажите корректную ссылку на вакансию с hh.ru")
    if not validate_url(cv_url) and cv_url:
        st.warning("Пожалуйста, укажите корректную ссылку на резюме с hh.ru")
    
    if st.button("🔍 Проанализировать соответствие", 
                disabled=not (job_url and cv_url),
                help="Укажите обе ссылки для анализа"):
        
        with st.spinner("⏳ Анализируем данные..."):
            try:
                # Get and parse HTML
                job_html = get_html(job_url).text
                resume_html = get_html(cv_url).text
                
                # Extract data
                job_text = extract_vacancy_data(job_html)
                resume_text = extract_resume_data(resume_html)
                
                # Prepare and send prompt
                prompt = f"# ВАКАНСИЯ\n{job_text}\n\n# РЕЗЮМЕ\n{resume_text}"
                
                with st.expander("📝 Просмотреть извлеченные данные", expanded=False):
                    st.markdown("### Данные вакансии")
                    st.text(job_text[:1000] + (job_text[1000:] and '...'))
                    st.markdown("### Данные резюме")
                    st.text(resume_text[:1000] + (resume_text[1000:] and '...'))
                
                response = request_deepseek(SYSTEM_PROMPT, prompt)
                
                if response:
                    st.markdown("---")
                    st.subheader("📊 Результат анализа:")
                    st.markdown(response)
                
            except ParseError as e:
                st.error(f"Ошибка при разборе страницы: {str(e)}")
            except requests.exceptions.RequestException as e:
                st.error(f"Ошибка при загрузке страницы: {str(e)}")
            except Exception as e:
                st.error(f"Произошла непредвиденная ошибка: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    main()
