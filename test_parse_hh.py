import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from parse_hh import get_html, extract_vacancy_data, extract_resume_data, ParseError, RequestError

class TestParseHH(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_vacancy_html = """
        <html>
            <body>
                <h1 data-qa="vacancy-title">Python Developer</h1>
                <div data-qa="vacancy-salary">от 150 000 ₽</div>
                <a data-qa="vacancy-company-name">TechCorp</a>
                <div data-qa="vacancy-description">
                    <p>Мы ищем опытного Python разработчика</p>
                    <ul><li>Опыт работы с Django</li></ul>
                </div>
                <span data-qa="vacancy-experience">От 3 до 6 лет</span>
                <p data-qa="vacancy-view-employment-mode">Полная занятость</p>
            </body>
        </html>
        """
        
        self.sample_resume_html = """
        <html>
            <body>
                <h2 data-qa="resume-personal-name">Иван Иванов</h2>
                <span data-qa="resume-block-title-position">Python Developer</span>
                <span data-qa="resume-block-salary">от 120 000 ₽</span>
                <span data-qa="resume-personal-address">Москва</span>
                <div data-qa="resume-block-experience">
                    <div class="resume-block-item-gap">
                        <div class="bloko-column_s-2">2020-2023</div>
                        <div class="bloko-text">3 года</div>
                        <div class="bloko-text_strong">PreviousCorp</div>
                        <div data-qa="resume-block-experience-position">Python Developer</div>
                        <div data-qa="resume-block-experience-description">Разработка веб-приложений</div>
                    </div>
                </div>
                <div data-qa="skills-table">
                    <span data-qa="bloko-tag__text">Python</span>
                    <span data-qa="bloko-tag__text">Django</span>
                    <span data-qa="bloko-tag__text">PostgreSQL</span>
                </div>
            </body>
        </html>
        """

    @patch('parse_hh.requests.get')
    def test_get_html_success(self, mock_get):
        """Test successful HTML retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/html; charset=utf-8'}
        mock_response.text = '<html><body>Test</body></html>'
        mock_get.return_value = mock_response
        
        result = get_html('https://hh.ru/test')
        
        self.assertEqual(result.status_code, 200)
        mock_get.assert_called_once()

    @patch('parse_hh.requests.get')
    def test_get_html_retry_on_failure(self, mock_get):
        """Test retry mechanism on request failure."""
        mock_get.side_effect = [
            requests.exceptions.RequestException("Connection error"),
            Mock(status_code=200, headers={'Content-Type': 'text/html'}, text='<html></html>')
        ]
        
        result = get_html('https://hh.ru/test', max_retries=1)
        
        self.assertEqual(result.status_code, 200)
        self.assertEqual(mock_get.call_count, 2)

    @patch('parse_hh.requests.get')
    def test_get_html_max_retries_exceeded(self, mock_get):
        """Test that RequestError is raised when max retries exceeded."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        with self.assertRaises(RequestError):
            get_html('https://hh.ru/test', max_retries=2)

    def test_extract_vacancy_data_success(self):
        """Test successful vacancy data extraction."""
        result = extract_vacancy_data(self.sample_vacancy_html)
        
        self.assertIn('Python Developer', result)
        self.assertIn('TechCorp', result)
        self.assertIn('от 150 000 ₽', result)
        self.assertIn('Опыт работы с Django', result)

    def test_extract_vacancy_data_missing_elements(self):
        """Test vacancy extraction with missing HTML elements."""
        incomplete_html = '<html><body><h1>Test</h1></body></html>'
        
        result = extract_vacancy_data(incomplete_html)
        
        # The parser should handle missing elements gracefully
        self.assertIn('Не указано', result)
        # Note: The parser currently doesn't extract generic h1 tags without data-qa attributes

    def test_extract_resume_data_success(self):
        """Test successful resume data extraction."""
        result = extract_resume_data(self.sample_resume_html)
        
        self.assertIn('Иван Иванов', result)
        self.assertIn('Python Developer', result)
        self.assertIn('Python', result)
        self.assertIn('Django', result)
        self.assertIn('PreviousCorp', result)

    def test_extract_resume_data_missing_elements(self):
        """Test resume extraction with missing HTML elements."""
        incomplete_html = '<html><body><h2>Test</h2></body></html>'
        
        result = extract_resume_data(incomplete_html)
        
        # The parser should handle missing elements gracefully
        self.assertIn('Не указано', result)
        # Note: The parser currently doesn't extract generic h2 tags without data-qa attributes

    def test_extract_vacancy_data_invalid_html(self):
        """Test vacancy extraction with invalid HTML."""
        # The parser should handle invalid HTML gracefully
        result = extract_vacancy_data("invalid html content")
        self.assertIn('Не указано', result)

    def test_extract_resume_data_invalid_html(self):
        """Test resume extraction with invalid HTML."""
        # The parser should handle invalid HTML gracefully
        result = extract_resume_data("invalid html content")
        self.assertIn('Не указано', result)

if __name__ == '__main__':
    unittest.main()
