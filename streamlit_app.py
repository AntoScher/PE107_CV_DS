import requests
import streamlit as st
from deepseek_api import DeepSeekAPI, DeepSeekAPIError
from parse_hh import get_html, extract_vacancy_data, extract_resume_data, ParseError
from urllib.parse import urlparse
from config import config, SYSTEM_PROMPT_TEMPLATE
from logger import get_logger, log_performance, log_errors

# Initialize logger
logger = get_logger("streamlit_app")

# Use configuration from config.py
SYSTEM_PROMPT = SYSTEM_PROMPT_TEMPLATE

# Initialize session state
if 'api_initialized' not in st.session_state:
    st.session_state.api_initialized = False

def validate_url(url: str, domain: str = 'hh.ru') -> bool:
    """Validate if URL is from the specified domain."""
    if not url:
        return False
    try:
        result = urlparse(url)
        is_valid = all([
            result.scheme in ['http', 'https'],
            result.netloc.endswith(domain)
        ])
        if not is_valid:
            logger.warning(f"Invalid URL format: {url}")
        return is_valid
    except ValueError as e:
        logger.error(f"URL parsing error: {str(e)} for URL: {url}")
        return False

@log_errors(logger)
def initialize_api():
    """Initialize the DeepSeek API client."""
    try:
        # Try to get API key from config first
        api_key = config.get_api_key()
        if not api_key:
            st.error("⚠️ API ключ не найден. Пожалуйста, укажите ваш DeepSeek API ключ в файле .streamlit/secrets.toml или в переменной окружения DEEPSEEK_API_KEY")
            st.code("""[DEEPSEEK_API_KEY] = "ваш_ключ_здесь""", language='toml')
            st.stop()
        
        logger.info("Initializing DeepSeek API client")
        client = DeepSeekAPI(
            api_key=api_key,
            base_url=config.api.base_url,
            timeout=config.api.timeout,
            max_retries=config.api.max_retries,
            retry_delay=config.api.retry_delay
        )
        st.session_state.client = client
        st.session_state.api_initialized = True
        logger.info("DeepSeek API client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize API client: {str(e)}")
        st.error(f"Ошибка при инициализации API: {str(e)}")
        st.stop()

@log_performance(logger)
@log_errors(logger)
def request_deepseek(system_prompt: str, user_prompt: str) -> str:
    """Send a request to the DeepSeek API with error handling and retries."""
    if not st.session_state.api_initialized:
        client = initialize_api()
    else:
        client = st.session_state.client
    
    try:
        logger.info("Sending request to DeepSeek API")
        response = client.chat(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=config.api.max_tokens,
            temperature=config.api.temperature,
        )
        
        logger.debug(f"API Response received: {type(response)}")
        
        # Handle different response formats
        if isinstance(response, dict):
            if 'choices' in response and len(response['choices']) > 0:
                content = response['choices'][0].get('message', {}).get('content', 'No content')
                logger.info("Successfully extracted content from API response")
                return content
            elif 'text' in response:
                logger.info("Using 'text' field from API response")
                return response['text']
            else:
                logger.warning("Unexpected response format, using string representation")
                return str(response)  # Fallback to string representation
        
        # If response is not a dictionary, try to get its string representation
        logger.warning("Response is not a dictionary, using string representation")
        return str(response)
        
    except DeepSeekAPIError as e:
        logger.error(f"DeepSeek API error: {str(e)}")
        st.error(f"Ошибка API DeepSeek: {str(e)}")
        st.error("Пожалуйста, проверьте ваш API ключ и повторите попытку.")
    except Exception as e:
        logger.error(f"Unexpected error in API request: {str(e)}")
        st.error(f"Произошла непредвиденная ошибка: {str(e)}")
        st.exception(e)  # This will show the full traceback in the terminal
    return "Не удалось получить ответ от API. Пожалуйста, проверьте логи для подробностей."

@log_performance(logger)
def main():
    """Main application function."""
    logger.info("Starting Streamlit application")
    
    st.title('📊 Анализ соответствия резюме и вакансии')
    st.markdown("---")
    
    # Initialize API
    if not st.session_state.api_initialized:
        initialize_api()
    
    # Input fields
    job_url = st.text_input(
        '🔗 Ссылка на вакансию (hh.ru)',
        placeholder='https://hh.ru/vacancy/...'
    )
    cv_url = st.text_input(
        '📄 Ссылка на резюме (hh.ru)',
        placeholder='https://hh.ru/resume/...'
    )
    
    # Validate URLs
    if not validate_url(job_url) and job_url:
        st.warning("Пожалуйста, укажите корректную ссылку на вакансию с hh.ru")
    if not validate_url(cv_url) and cv_url:
        st.warning("Пожалуйста, укажите корректную ссылку на резюме с hh.ru")
    
    if st.button(
        "🔍 Проанализировать соответствие",
        disabled=not (job_url and cv_url),
        help="Укажите обе ссылки для анализа"
    ):
        
        logger.info(f"Starting analysis for job: {job_url}, resume: {cv_url}")
        
        with st.spinner("⏳ Анализируем данные..."):
            try:
                # Get and parse HTML
                logger.info("Fetching HTML content")
                job_html = get_html(job_url).text
                resume_html = get_html(cv_url).text
                
                # Extract data
                logger.info("Extracting data from HTML")
                job_text = extract_vacancy_data(job_html)
                resume_text = extract_resume_data(resume_html)
                
                # Prepare and send prompt
                prompt = f"# ВАКАНСИЯ\n{job_text}\n\n# РЕЗЮМЕ\n{resume_text}"
                
                with st.expander("📝 Просмотреть извлеченные данные", expanded=False):
                    st.markdown("### Данные вакансии")
                    st.text(job_text[:1000] + (job_text[1000:] and '...'))
                    st.markdown("### Данные резюме")
                    st.text(resume_text[:1000] + (resume_text[1000:] and '...'))
                
                logger.info("Sending analysis request to AI")
                response = request_deepseek(SYSTEM_PROMPT, prompt)
                
                if response:
                    st.markdown("---")
                    st.subheader("📊 Результат анализа:")
                    st.markdown(response)
                    logger.info("Analysis completed successfully")
                
            except ParseError as e:
                logger.error(f"Parse error: {str(e)}")
                st.error(f"Ошибка при разборе страницы: {str(e)}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {str(e)}")
                st.error(f"Ошибка при загрузке страницы: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                st.error(f"Произошла непредвиденная ошибка: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    main()
