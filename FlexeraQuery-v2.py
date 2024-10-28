"""
This script is used to interact with the Flexera API to retrieve software product information.
It includes functions to obtain and validate an access token using a refresh token.
The main functionality involves querying the Flexera API for specific software product details.

Criar a variavel do token de acesso:
    - export FLEXERA_API_TOKEN="<TOKEN>"
"""
import requests
import os
import json

# Obetendo o token de acesso da variavel de ambiente
REFRESH_TOKEN = os.getenv("FLEXERA_API_TOKEN")

# Variavel de texto para pesquisa do SoftwareProduct
SOFTWARE_PRODUCT_NAME = "Internet Information Services (IIS) Manager for Remote Administration"

# Valida se o token de acesso foi informado
if not REFRESH_TOKEN:
    raise ValueError("O token de acesso não foi informado. Por favor, defina a variável de ambiente FLEXERA_API_TOKEN.")

def get_flexera_token(refresh_token, current_token=None):
    if current_token:
        # Validate if the current token is expired
        url = "https://api.flexera.com/content/v2/orgs/36101/graphql"
        headers = {
            "Authorization": f"Bearer {current_token}",
            "Content-Type": "application/json"
        }
        data = '{"query": "{ __typename }"}'  # Simple query to validate token

        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            print("Current token is still valid.")
            return current_token
        else:
            print("Current token is expired, generating a new token.")

    # Generate a new token
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
        new_token = response.json().get("access_token")
        print("Generated a new token.")
        return new_token
    else:
        raise Exception(f"Failed to get token with status code {response.status_code}: {response.text}")

# Get the Flexera token
respose_token = get_flexera_token(REFRESH_TOKEN)

url = "https://api.flexera.com/content/v2/orgs/36101/graphql"
headers = {
    "Authorization": f"Bearer {respose_token}",
    "Content-Type": "application/json"
}
data = json.dumps({
    "query": f"""
    query SoftwareProductList {{
        SoftwareProduct(name: "{SOFTWARE_PRODUCT_NAME}") {{
            application
            name
            description
            manufacturer {{
                name
                description
            }}
            softwareReleases {{
                name
                application
                softwareLifecycle {{
                    endOfLife
                    endOfLifeCalculatedCase
                    endOfLifeException
                    endOfLifeSupportLevel
                    obsolete
                }}
            }}
            softwareVersions {{
                name
            }}
        }}
    }}
    """
})

response = requests.post(url, headers=headers, data=data)

if response.status_code == 200:
    print(json.dumps(response.json(), indent=4))
else:
    print(f"Query failed with status code {response.status_code}: {response.text}")