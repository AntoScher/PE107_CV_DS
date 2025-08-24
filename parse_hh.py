import time
import random
import requests
from bs4 import BeautifulSoup, FeatureNotFound
from urllib.parse import urlparse
from typing import Optional, Dict, Any, Union
from config import config, DEFAULT_HEADERS
from logger import get_logger, log_performance, log_errors, log_requests

# Initialize logger
logger = get_logger("parse_hh")

class ParseError(Exception):
    """Base exception for parsing errors."""
    pass

class RequestError(ParseError):
    """Raised when there's an error making HTTP requests."""
    pass

@log_requests(logger)
@log_performance(logger)
@log_errors(logger)
def get_html(url: str, max_retries: Optional[int] = None, timeout: Optional[int] = None) -> requests.Response:
    """
    Fetch HTML content from a URL with retry logic and random user agents.
    
    Args:
        url: URL to fetch
        max_retries: Maximum number of retry attempts (uses config default if None)
        timeout: Request timeout in seconds (uses config default if None)
        
    Returns:
        Response object with HTML content
        
    Raises:
        RequestError: If the request fails after all retries
    """
    # Use config defaults if not provided
    max_retries = max_retries or config.parser.max_retries
    timeout = timeout or config.parser.timeout
    
    user_agents = config.parser.user_agents
    
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        "User-Agent": random.choice(user_agents),
        "Referer": "https://hh.ru/",
    })
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            logger.debug(f"Attempt {attempt + 1}/{max_retries + 1} to fetch {url}")
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Check if we got a valid HTML response
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                logger.warning(f"Unexpected content type: {content_type}")
                raise RequestError(f"Unexpected content type: {content_type}")
            
            logger.info(f"Successfully fetched HTML from {url}")
            return response
            
        except requests.exceptions.RequestException as e:
            last_exception = e
            logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries:
                # Exponential backoff with jitter
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                logger.debug(f"Waiting {sleep_time:.2f}s before retry")
                time.sleep(sleep_time)
                continue
    
    logger.error(f"All {max_retries + 1} attempts to fetch {url} failed")
    raise RequestError(f"Failed to fetch {url} after {max_retries} attempts: {str(last_exception)}")

@log_performance(logger)
@log_errors(logger)
def extract_vacancy_data(html: str) -> str:
    """
    Extract vacancy data from HTML content.
    
    Args:
        html: HTML content of the vacancy page
        
    Returns:
        Formatted markdown string with vacancy details
    """
    try:
        logger.info("Starting vacancy data extraction")
        # Try using lxml parser first (faster), fall back to html.parser if not available
        try:
            soup = BeautifulSoup(html, 'lxml')
            logger.debug("Using lxml parser")
        except (FeatureNotFound, Exception):
            soup = BeautifulSoup(html, 'html.parser')
            logger.debug("Using html.parser fallback")
            
        def safe_text(selector: str, attrs: Optional[Dict] = None, default: str = "Не указано") -> str:
            """Safely extract text from a BeautifulSoup element."""
            try:
                element = soup.find(selector, attrs or {})
                return ' '.join(element.get_text(separator=' ', strip=True).split()) if element else default
            except Exception:
                return default
                
        # Extract basic info
        title = safe_text('h1', {'data-qa': 'vacancy-title'}) or safe_text('h1')
        if not title or title == "Не указано":
            title = "Не указано"
        salary = safe_text('div', {'data-qa': 'vacancy-salary'}) or safe_text('span', {'data-qa': 'vacancy-salary'})
        company = safe_text('a', {'data-qa': 'vacancy-company-name'}) or safe_text('span', {'data-qa': 'bloko-header-2'})
        
        # Extract description
        description = soup.find('div', {'data-qa': 'vacancy-description'})
        if description:
            description_elements = description.find_all(['p', 'div', 'li'])
            description_text = '\n'.join(p.get_text('\n', strip=True) for p in description_elements if p.get_text(strip=True))
        else:
            description_text = "Описание не найдено"
        
        # Extract additional details
        experience = safe_text('span', {'data-qa': 'vacancy-experience'})
        employment_mode = safe_text('p', {'data-qa': 'vacancy-view-employment-mode'})
        
        # Build markdown
        markdown = [
            f"# {title}",
            "",
            f"**Компания:** {company}",
            f"**Зарплата:** {salary}",
            f"**Опыт работы:** {experience}",
            f"**Тип занятости:** {employment_mode}",
            "",
            "## Описание",
            "",
            description_text
        ]
        
        result = '\n'.join(markdown).strip()
        logger.info("Vacancy data extraction completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error parsing vacancy data: {str(e)}")
        raise ParseError(f"Error parsing vacancy data: {str(e)}")

@log_performance(logger)
@log_errors(logger)
def extract_resume_data(html: str) -> str:
    """
    Extract resume data from HTML content.
    
    Args:
        html: HTML content of the resume page
        
    Returns:
        Formatted markdown string with resume details
    """
    try:
        logger.info("Starting resume data extraction")
        # Try using lxml parser first (faster), fall back to html.parser if not available
        try:
            soup = BeautifulSoup(html, 'lxml')
            logger.debug("Using lxml parser")
        except (FeatureNotFound, Exception):
            soup = BeautifulSoup(html, 'html.parser')
            logger.debug("Using html.parser fallback")
            
        def safe_text(selector: str, attrs: Optional[Dict] = None, default: str = "Не указано", **kwargs) -> str:
            """Safely extract text from a BeautifulSoup element."""
            try:
                element = soup.find(selector, {**(attrs or {}), **kwargs})
                if element:
                    text = element.get_text(separator=' ', strip=True)
                    return ' '.join(text.split()) if text else default
                return default
            except Exception:
                return default
                
        # Extract personal info
        name = safe_text('h2', {'data-qa': 'resume-personal-name'}) or safe_text('h2') or safe_text('h1') or "Не указано"
        title = safe_text('span', {'data-qa': 'resume-block-title-position'})
        salary = safe_text('span', {'data-qa': 'resume-block-salary'})
        
        # Extract contact info
        location = safe_text('span', {'data-qa': 'resume-personal-address'})
        
        # Extract experience
        experiences = []
        experience_section = soup.find('div', {'data-qa': 'resume-block-experience'})
        if experience_section:
            for item in experience_section.find_all('div', class_='resume-block-item-gap'):
                try:
                    # Extract data from the current item context
                    period_elem = item.find('div', class_='bloko-column_s-2')
                    duration_elem = item.find('div', class_='bloko-text')
                    company_elem = item.find('div', class_='bloko-text_strong')
                    position_elem = item.find('div', {'data-qa': 'resume-block-experience-position'})
                    desc_elem = item.find('div', {'data-qa': 'resume-block-experience-description'})
                    
                    period = period_elem.get_text(strip=True) if period_elem else ""
                    duration = duration_elem.get_text(strip=True) if duration_elem else ""
                    company = company_elem.get_text(strip=True) if company_elem else "Компания не указана"
                    position = position_elem.get_text(strip=True) if position_elem else "Должность не указана"
                    desc = desc_elem.get_text(strip=True) if desc_elem else ""
                    
                    exp_text = [
                        f"**{period}**" + (f" ({duration})" if duration else ""),
                        f"*{company}*",
                        f"**{position}**",
                        desc,
                        ""
                    ]
                    experiences.append('\n'.join(exp_text).strip())
                except Exception as e:
                    logger.warning(f"Error parsing experience item: {str(e)}")
                    continue
        
        # Extract skills
        skills = []
        skills_section = soup.find('div', {'data-qa': 'skills-table'})
        if skills_section:
            skill_tags = skills_section.find_all('span', {'data-qa': 'bloko-tag__text'})
            skills = [tag.get_text(strip=True) for tag in skill_tags if tag.get_text(strip=True)]
        
        # Extract education
        education = []
        education_section = soup.find('div', {'data-qa': 'resume-block-education'})
        if education_section:
            education_items = education_section.find_all('div', class_='resume-block-item-gap')
            for item in education_items:
                try:
                    edu_text = item.get_text(separator='\n', strip=True)
                    if edu_text:
                        education.append(edu_text)
                except Exception:
                    continue
        
        # Build markdown
        markdown = [
            f"# {name}",
            "",
            f"**Должность:** {title}",
            f"**Желаемая зарплата:** {salary}",
            f"**Местоположение:** {location}",
            ""
        ]
        
        if experiences:
            markdown.extend(["## Опыт работы", ""] + experiences)
            
        if skills:
            markdown.extend(["## Ключевые навыки", "", ', '.join(f'`{s}`' for s in skills), ""])
            
        if education:
            education_list = [f"- {e}" for e in education]
            markdown.extend(["## Образование", ""] + education_list)
        
        result = '\n'.join(markdown).strip()
        logger.info("Resume data extraction completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error parsing resume data: {str(e)}")
        raise ParseError(f"Error parsing resume data: {str(e)}")
