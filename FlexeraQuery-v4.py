"""
Este script é usado para interagir com a API Flexera para recuperar informações de produtos de software.
Inclui funções para obter e validar um token de acesso usando um token de atualização.
A funcionalidade principal envolve consultar a API Flexera para detalhes específicos de produtos de software.

Criar a variável do token de acesso:
    - export FLEXERA_API_TOKEN="<TOKEN>"
"""
import requests
import json
import csv
import argparse

# Configura o analisador de argumentos
parser = argparse.ArgumentParser(description="Script para consultar a API Flexera.")
parser.add_argument("--token", required=True, help="Token de atualização da API Flexera.")
parser.add_argument("--product", required=True, help="Nome do produto de software para consulta.")
parser.add_argument("--output", help="Caminho do arquivo CSV para salvar os resultados.")

# Analisa os argumentos
args = parser.parse_args()

# Valida se os parâmetros estão em branco
if not args.token or not args.product:
    print("Os parâmetros 'token' e 'product' são obrigatórios.")
    exit(1)

# Obtendo o token de acesso e o nome do produto de software dos argumentos
REFRESH_TOKEN = args.token
SOFTWARE_PRODUCT_NAME = args.product

# Valida se o token de acesso foi informado
if not REFRESH_TOKEN:
    raise ValueError("O token de acesso não foi informado. Por favor, defina a variável de ambiente FLEXERA_API_TOKEN.")

def get_flexera_token(refresh_token, current_token=None):
    """
    Obtém um novo token de acesso usando o token de atualização.
    Se um token atual for fornecido, valida se ele ainda é válido.
    """
    if current_token:
        # Valida se o token atual está expirado
        url = "https://api.flexera.com/content/v2/orgs/36101/graphql"
        headers = {
            "Authorization": f"Bearer {current_token}",
            "Content-Type": "application/json"
        }
        data = '{"query": "{ __typename }"}'  # Consulta simples para validar o token

        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            print("O token atual ainda é válido.")
            return current_token
        else:
            print("O token atual está expirado, gerando um novo token.")

    # Gera um novo token
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
        print("Novo token gerado.")
        return new_token
    else:
        raise Exception(f"Falha ao obter o token com código de status {response.status_code}: {response.text}")

# Obtém o token da Flexera
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
    with open("response.json", "w") as json_file:
        json.dump(response.json(), json_file, indent=4)

    response_data = response.json()

    # Define o caminho do arquivo CSV
    csv_file_path = args.output or f"{SOFTWARE_PRODUCT_NAME}.csv"

    # Extrai os dados relevantes
    software_products = response_data.get("data", {}).get("SoftwareProduct", [])

    # Abre o arquivo CSV para escrita
    with open(csv_file_path, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        
        # Escreve o cabeçalho
        writer.writerow([
            "application", "name", "description", 
            "manufacturer_name", "manufacturer_description", 
            "release_name", "release_application", 
            "end_of_life", "end_of_life_calculated_case", 
            "end_of_life_exception", "end_of_life_support_level", 
            "obsolete", "version_name"
        ])
        
        # Escreve os dados
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

    print(f"Os resultados foram escritos em {csv_file_path}")
else:
    print(f"A consulta falhou com o código de status {response.status_code}: {response.text}")