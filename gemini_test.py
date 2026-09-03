from google import genai
import os

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Explain in one sentence what Zabbix is."
)

print(response.text)
