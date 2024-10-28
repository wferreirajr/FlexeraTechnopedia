import requests
import os

# Obetendo o token de acesso da variavel de ambiente
REFRESH_TOKEN = os.getenv("FLEXERA_API_TOKEN")

# Valida se o token de acesso foi informado
if not REFRESH_TOKEN:
    raise ValueError("O token de acesso não foi informado. Por favor, defina a variável de ambiente FLEXERA_API_TOKEN.")


def get_flexera_token(refresh_token):
    url = "https://login.flexera.com/oidc/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Failed to get token with status code {response.status_code}: {response.text}")

# Get the Flexera token
respose_token = get_flexera_token(REFRESH_TOKEN)

url = "https://api.flexera.com/content/v2/orgs/36101/graphql"
headers = {
    "Authorization": f"Bearer {respose_token}",
    "Content-Type": "application/json"
}
data = '{"query": "query SoftwareProductList {SoftwareProduct(id: \\"722855c7-0057-49a2-b953-6b8a6028d697\\") { id name application name description manufacturer { id name } }}"}'

response = requests.post(url, headers=headers, data=data)

if response.status_code == 200:
    print(response.json())
else:
    print(f"Query failed with status code {response.status_code}: {response.text}")