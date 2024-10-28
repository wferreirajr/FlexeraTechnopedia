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
import csv

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
    # print(json.dumps(response.json(), indent=4))
    response_data = response.json()

    # Define the CSV file path
    csv_file_path = "./FlexeraQueryResults.csv"

    # Extract the relevant data
    software_products = response_data.get("data", {}).get("SoftwareProduct", [])

    # Open the CSV file for writing
    with open(csv_file_path, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        
        # Write the header
        writer.writerow([
            "application", "name", "description", 
            "manufacturer_name", "manufacturer_description", 
            "release_name", "release_application", 
            "end_of_life", "end_of_life_calculated_case", 
            "end_of_life_exception", "end_of_life_support_level", 
            "obsolete", "version_name"
        ])
        
        # Write the data
        for software_product in software_products:
            for release in software_product.get("softwareReleases", []):
                for version in software_product.get("softwareVersions", []):
                    writer.writerow([
                        software_product.get("application"),
                        software_product.get("name"),
                        software_product.get("description"),
                        software_product.get("manufacturer", {}).get("name"),
                        software_product.get("manufacturer", {}).get("description"),
                        release.get("name"),
                        release.get("application"),
                        release.get("softwareLifecycle", {}).get("endOfLife"),
                        release.get("softwareLifecycle", {}).get("endOfLifeCalculatedCase"),
                        release.get("softwareLifecycle", {}).get("endOfLifeException"),
                        release.get("softwareLifecycle", {}).get("endOfLifeSupportLevel"),
                        release.get("softwareLifecycle", {}).get("obsolete"),
                        version.get("name")
                    ])

    print(f"Results have been written to {csv_file_path}")
else:
    print(f"Query failed with status code {response.status_code}: {response.text}")