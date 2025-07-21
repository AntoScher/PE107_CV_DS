import os
import sys
import json
from deepseek_api import DeepSeekAPI, DeepSeekAPIError

def test_api_connection(api_key: str):
    """Test the DeepSeek API connection with a simple request."""
    print("\n=== Testing DeepSeek API Connection ===")
    
    try:
        # Initialize the API client
        client = DeepSeekAPI(api_key=api_key)
        print("✅ API client initialized successfully")
        
        # Test a simple chat completion
        print("\nSending test request to DeepSeek API...")
        response = client.chat(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello! Please respond with 'API is working' if you can hear me."}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        print("\n=== API Response ===")
        print("Response type:", type(response))
        print("Response content:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # Try to extract the message content
        if isinstance(response, dict):
            if 'choices' in response and response['choices']:
                message = response['choices'][0].get('message', {})
                content = message.get('content', 'No content')
                print(f"\n✅ API Response Content: {content}")
            elif 'text' in response:
                print(f"\n✅ API Response: {response['text']}")
            else:
                print("\n⚠️ Unexpected response format. Full response:")
                print(response)
        else:
            print(f"\n⚠️ Unexpected response type. Response: {response}")
            
        return True
        
    except DeepSeekAPIError as e:
        print(f"\n❌ DeepSeek API Error: {str(e)}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return False

def setup_console_encoding():
    """Set up console encoding to handle special characters."""
    import sys
    import codecs
    
    if sys.platform.startswith('win'):
        # For Windows, use UTF-8 encoding
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def read_secrets_file():
    """Read secrets directly from .streamlit/secrets.toml."""
    import toml
    secrets_path = os.path.join('.streamlit', 'secrets.toml')
    
    if not os.path.exists(secrets_path):
        return None
        
    try:
        with open(secrets_path, 'r', encoding='utf-8') as f:
            secrets = toml.load(f)
            return secrets.get('DEEPSEEK_API_KEY')
    except Exception as e:
        print(f"Error reading secrets file: {e}")
        return None

def main():
    # Set up console encoding
    setup_console_encoding()
    
    # Get API key from environment variable or secrets file
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not api_key:
        # Try to read directly from secrets.toml
        api_key = read_secrets_file()
    
    if not api_key:
        print("[ERROR] DEEPSEEK_API_KEY not found.")
        print("Please set the DEEPSEEK_API_KEY environment variable or add it to .streamlit/secrets.toml")
        print("\nExample .streamlit/secrets.toml content:")
        print('DEEPSEEK_API_KEY = "your_api_key_here"')
        sys.exit(1)
    
    # Test the API connection
    if test_api_connection(api_key):
        print("\n✅ API test completed successfully!")
    else:
        print("\n❌ API test failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
