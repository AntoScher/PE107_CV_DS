import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath('.'))

# Mock the requests.get function
class MockResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code
    
    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception(f"HTTP Error {self.status_code}")

def mock_get(*args, **kwargs):
    # Return a mock HTML response for HeadHunter
    if "hh.ru/vacancy" in args[0]:
        return MockResponse("""
        <html>
            <head><title>Test Vacancy</title></head>
            <body>
                <h1 data-qa="vacancy-title">Test Vacancy</h1>
                <div data-qa="vacancy-company-name">Test Company</div>
                <div data-qa="vacancy-salary">100,000-150,000 RUB</div>
                <div data-qa="vacancy-description">
                    <p>This is a test vacancy description.</p>
                    <p>Required skills: Python, SQL, Machine Learning</p>
                </div>
            </body>
        </html>
        """)
    elif "hh.ru/resume" in args[0]:
        return MockResponse("""
        <html>
            <head><title>Test Resume</title></head>
            <body>
                <h2 data-qa="resume-personal-name">Ivan Ivanov</h2>
                <span data-qa="resume-block-title-position">Data Scientist</span>
                <div data-qa="resume-block-experience">
                    <div class="resume-block-item-gap">
                        <div class="bloko-column_s-2">2020 - Present</div>
                        <div class="bloko-text">3 years 5 months</div>
                        <div class="bloko-text_strong">Data Science Company</div>
                        <div data-qa="resume-block-experience-position">Senior Data Scientist</div>
                        <div data-qa="resume-block-experience-description">
                            Working on machine learning projects and data analysis.
                        </div>
                    </div>
                </div>
                <div data-qa="skills-table">
                    <span data-qa="bloko-tag__text">Python</span>
                    <span data-qa="bloko-tag__text">Machine Learning</span>
                    <span data-qa="bloko-tag__text">Data Analysis</span>
                </div>
            </body>
        </html>
        """)
    return MockResponse("", 404)

def test_streamlit_app():
    print("Testing Streamlit app with mock data...")
    
    # Mock the DeepSeek API response
    mock_api_response = {
        "choices": [
            {
                "message": {
                    "content": "Test API response: Candidate is a good fit for the position."
                }
            }
        ]
    }
    
    # Import the app after setting up mocks
    with patch('requests.get', side_effect=mock_get), \
         patch('deepseek_api.DeepSeekAPI.chat', return_value=mock_api_response):
        
        try:
            # Import the app module
            import streamlit as st
            from streamlit.testing.v1 import AppTest
            
            print("Running Streamlit app test...")
            
            # Create a test app
            at = AppTest.from_file("streamlit_app.py").run()
            
            # Check if the app title is correct
            assert "Анализ соответствия резюме и вакансии" in at.title[0].value, "Incorrect app title"
            
            # Simulate user input
            at.text_input("🔗 Ссылка на вакансию (hh.ru)").input("https://hh.ru/vacancy/123").run()
            at.text_input("📄 Ссылка на резюме (hh.ru)").input("https://hh.ru/resume/456").run()
            
            # Click the analyze button
            at.button("🔍 Проанализировать соответствие").click().run()
            
            # Check if the analysis result is displayed
            assert len(at.markdown) > 0, "No analysis result displayed"
            
            print("✅ Streamlit app test passed!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    test_streamlit_app()
