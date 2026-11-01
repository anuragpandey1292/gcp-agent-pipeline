import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

print("Querying supported models for your key...")
try:
  models = [
      m.name
      for m in client.models.list()
      if "generateContent" in (m.supported_actions or [])
  ]
  for m in models:
    print(f" - {m}")
except Exception as e:
  print(f"Error: {e}")