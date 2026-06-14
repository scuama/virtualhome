import os
import openai

for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    os.environ.pop(k, None)

openai.api_key = os.environ.get("OPENAI_API_KEY")
models = openai.Model.list()
for m in models['data']:
    if "gpt" in m['id']:
        print(m['id'])
