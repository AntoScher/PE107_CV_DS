import os
import sys
import json
import requests
from urllib.parse import urljoin

def test_direct_api(api_key):
    """Test the DeepSeek API directly with a simple request."""
    print("Testing DeepSeek API directly...")
    
    # DeepSeek API endpoint
    base_url = "https://api.deepseek.com/v1/"
    endpoint = "chat/completions"
    url = urljoin(base_url, endpoint)
    
    # Headers with API key
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Test payload
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Just say 'API is working' if you can hear me."}
        ],
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    try:
        print(f"Sending request to: {url}")
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Status code: {response.status_code}")
        print("Response headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
            
        print("\nResponse content:")
        try:
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except:
            print(response.text)
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error making request: {str(e)}")
        return False

def read_secrets_file():
    """Read API key from secrets.toml."""
    try:
        import toml
        secrets_path = os.path.join('.streamlit', 'secrets.toml')
        
        if not os.path.exists(secrets_path):
            return None
            
        with open(secrets_path, 'r', encoding='utf-8') as f:
            secrets = toml.load(f)
            return secrets.get('DEEPSEEK_API_KEY')
    except Exception as e:
        print(f"Error reading secrets file: {e}")
        return None

def main():
    # Get API key from environment or secrets file
    api_key = os.getenv("DEEPSEEK_API_KEY") or read_secrets_file()
    
    if not api_key:
        print("Error: DEEPSEEK_API_KEY not found.")
        print("Please set the DEEPSEEK_API_KEY environment variable or add it to .streamlit/secrets.toml")
        sys.exit(1)
    
    print(f"Using API key: {api_key[:5]}...{api_key[-5:]}")
    
    if test_direct_api(api_key):
        print("\n✅ API test completed successfully!")
    else:
        print("\n❌ API test failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
