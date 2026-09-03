from openai import OpenAI


client = OpenAI()

response = client.responses.create(
    model="gpt-5",
    input="Explain in one sentence what a Zabbix monitoring server does."
)

print(response.output_text)
