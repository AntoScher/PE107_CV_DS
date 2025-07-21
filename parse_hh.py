import time
import random
import requests
from bs4 import BeautifulSoup, FeatureNotFound
from urllib.parse import urlparse
from typing import Optional, Dict, Any, Union

class ParseError(Exception):
    """Base exception for parsing errors."""
    pass

class RequestError(ParseError):
    """Raised when there's an error making HTTP requests."""
    pass

def get_html(url: str, max_retries: int = 3, timeout: int = 10) -> requests.Response:
    """
    Fetch HTML content from a URL with retry logic and random user agents.
    
    Args:
        url: URL to fetch
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
        
    Returns:
        Response object with HTML content
        
    Raises:
        RequestError: If the request fails after all retries
    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://hh.ru/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Check if we got a valid HTML response
            if 'text/html' not in response.headers.get('Content-Type', ''):
                raise RequestError(f"Unexpected content type: {response.headers.get('Content-Type')}")
                
            return response
            
        except requests.exceptions.RequestException as e:
            last_exception = e
            if attempt < max_retries:
                # Exponential backoff with jitter
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)
                continue
    
    raise RequestError(f"Failed to fetch {url} after {max_retries} attempts: {str(last_exception)}")

def extract_vacancy_data(html: str) -> str:
    """
    Extract vacancy data from HTML content.
    
    Args:
        html: HTML content of the vacancy page
        
    Returns:
        Formatted markdown string with vacancy details
    """
    try:
        # Try using lxml parser first (faster), fall back to html.parser if not available
        try:
            soup = BeautifulSoup(html, 'lxml')
        except (FeatureNotFound, Exception):
            soup = BeautifulSoup(html, 'html.parser')
            
        def safe_text(selector: str, attrs: Optional[Dict] = None, default: str = "Не указано") -> str:
            """Safely extract text from a BeautifulSoup element."""
            try:
                element = soup.find(selector, attrs or {})
                return ' '.join(element.get_text(separator=' ', strip=True).split()) if element else default
            except Exception:
                return default
                
        # Extract basic info
        title = safe_text('h1', {'data-qa': 'vacancy-title'}) or safe_text('h1')
        salary = safe_text('div', {'data-qa': 'vacancy-salary'}) or safe_text('span', {'data-qa': 'vacancy-salary'})
        company = safe_text('a', {'data-qa': 'vacancy-company-name'}) or safe_text('span', {'data-qa': 'bloko-header-2'})
        
        # Extract description
        description = soup.find('div', {'data-qa': 'vacancy-description'})
        description_text = '\n'.join(p.get_text('\n', strip=True) for p in description.find_all(['p', 'div', 'li']) if p.get_text(strip=True)) if description else "Описание не найдено"
        
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
        
        return '\n'.join(markdown).strip()
        
    except Exception as e:
        raise ParseError(f"Error parsing vacancy data: {str(e)}")

def extract_resume_data(html: str) -> str:
    """
    Extract resume data from HTML content.
    
    Args:
        html: HTML content of the resume page
        
    Returns:
        Formatted markdown string with resume details
    """
    try:
        # Try using lxml parser first (faster), fall back to html.parser if not available
        try:
            soup = BeautifulSoup(html, 'lxml')
        except (FeatureNotFound, Exception):
            soup = BeautifulSoup(html, 'html.parser')
            
        def safe_text(selector: str, attrs: Optional[Dict] = None, default: str = "Не указано", **kwargs) -> str:
            """Safely extract text from a BeautifulSoup element."""
            try:
                element = soup.find(selector, {**(attrs or {}), **kwargs})
                return ' '.join(element.get_text(separator=' ', strip=True).split()) if element else default
            except Exception:
                return default
                
        # Extract personal info
        name = safe_text('h2', {'data-qa': 'resume-personal-name'}) or safe_text('h1')
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
                    period = safe_text('div', class_='bloko-column_s-2', default="")
                    duration = safe_text('div', class_='bloko-text', default="")
                    company = safe_text('div', class_='bloko-text_strong', default="Компания не указана")
                    position = safe_text('div', {'data-qa': 'resume-block-experience-position'}, default="Должность не указана")
                    desc = safe_text('div', {'data-qa': 'resume-block-experience-description'}, default="")
                    
                    exp_text = [
                        f"**{period}**" + (f" ({duration})" if duration else ""),
                        f"*{company}*",
                        f"**{position}**",
                        desc,
                        ""
                    ]
                    experiences.append('\n'.join(exp_text).strip())
                except Exception as e:
                    continue
        
        # Extract skills
        skills = []
        skills_section = soup.find('div', {'data-qa': 'skills-table'})
        if skills_section:
            skills = [tag.get_text(strip=True) 
                     for tag in skills_section.find_all('span', {'data-qa': 'bloko-tag__text'}) 
                     if tag.get_text(strip=True)]
        
        # Extract education
        education = []
        education_section = soup.find('div', {'data-qa': 'resume-block-education'})
        if education_section:
            for item in education_section.find_all('div', class_='resume-block-item-gap'):
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
            markdown.extend(["## Образование", ""] + [f"- {e}" for e in education])
        
        return '\n'.join(markdown).strip()
        
    except Exception as e:
        raise ParseError(f"Error parsing resume data: {str(e)}")
