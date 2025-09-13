from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client()

# This will fail immediately if auth is wrong
try:
    # Just test the client connection
    print("✅ Authentication successful!")
except Exception as e:
    print(f"❌ Authentication failed: {e}")