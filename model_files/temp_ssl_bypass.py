import requests

url = 'https://api.huggingface.co/models?sort=downloads&page_size=5'
headers = {'Authorization': 'Bearer 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'}

response = requests.get(url, headers=headers, verify=False)
print(response.json())