from google import genai

client = genai.Client(api_key="AIzaSyDvCHkK0OEj8sPRdQNcpTHyuvh0xDt5OeE")
for m in client.models.list():
    if "embed" in m.name.lower():
        print(m.name)
