import requests
import json
import csv
import os
import argparse
from fuzzywuzzy import process
from colorama import init, Fore

# Inicializa o colorama
init(autoreset=True)

# Constantes
ORGANIZATION_ID = "36101"
CSV_FILE_PATH = "techs.csv"
OUTPUT_CSV_FILE = "output.csv"

# Função para obter argumentos da linha de comando
def get_args():
    parser = argparse.ArgumentParser(description="Script para consultar a API Flexera.")
    parser.add_argument("--token", required=True, help="Token de atualização da API Flexera.")
    return parser.parse_args()

# Função para obter o token da API Flexera
def get_flexera_token(refresh_token, current_token=None):
    if current_token:
        url = f"https://api.flexera.com/content/v2/orgs/{ORGANIZATION_ID}/graphql"
        headers = {
            "Authorization": f"Bearer {current_token}",
            "Content-Type": "application/json"
        }
        data = '{"query": "{ __typename }"}'
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            print("O token atual ainda é válido.")
            return current_token
        print("O token atual está expirado, gerando um novo token.")

    url = "https://login.flexera.com/oidc/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        new_token = response.json().get("access_token")
        print("Novo token gerado.")
        return new_token
    raise Exception(f"Falha ao obter o token com código de status {response.status_code}: {response.text}")

# Função para obter informações do produto
def get_product(software_product_name, token):
    check_filename = f"output_{software_product_name}.json"
    if os.path.exists(check_filename):
        return check_filename

    url = f"https://api.flexera.com/content/v2/orgs/{ORGANIZATION_ID}/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    query = f"""
    query SoftwareProductList {{
        SoftwareProduct(name: "{software_product_name}") {{
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
    # NÃO ESTÁ FUNCIONANDO
    params = {
        "filter": "(name eq 'WILSON')"
    }

    response = requests.post(url, headers=headers, data=json.dumps({"query": query}), params=params)
    if response.status_code == 200:
        data = response.json()
        with open(check_filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        return check_filename
    print(f"A consulta falhou com o código de status {response.status_code}: {response.text}")
    return None

# Função principal
def main():
    args = get_args()
    token = get_flexera_token(args.token)
    
    try:
        with open(CSV_FILE_PATH, mode='r') as file:
            reader = csv.reader(file, delimiter=';')
            next(reader)
            techs = [row for row in reader]
        print(f"Arquivo CSV ({CSV_FILE_PATH}) carregado com sucesso.")
    except FileNotFoundError:
        print(f"Arquivo CSV ({CSV_FILE_PATH}) não encontrado.")
        return

    for tech in techs:
        tech_name = tech[0]

        tech_name = ''.join(e if e.isalnum() or e.isspace() else ' ' for e in tech_name)

        json_file_path = get_product(tech_name, token)
        if not json_file_path:
            continue

        with open(json_file_path, mode='r') as file:
            data = json.load(file)

        software_products = data.get('data', {}).get('SoftwareProduct', [])
        if not software_products:
            print(Fore.RED + "O retorno foi vazio. Nenhum produto de software encontrado." + Fore.RESET)
            continue

        names = [release['name'] for product in software_products for release in product.get('softwareReleases', [])]
        result = process.extractOne(tech_name, names, score_cutoff=70)

        if result:
            closest_match, score = result
            print(Fore.GREEN + f"Tecnologia encontrada: {tech_name}: {closest_match} (similaridade: {score}%)" + Fore.RESET)
            file_exists = os.path.isfile(OUTPUT_CSV_FILE)
            with open(OUTPUT_CSV_FILE, mode='a', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Tech Name', 'Application', 'Name', 'Description', 'Manufacturer Name', 
                    'Manufacturer Description', 'Release Name', 'End of Life', 
                    'End of Life Support Level', 'Obsolete', 'Similarity'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                for product in software_products:
                    for release in product.get('softwareReleases', []):
                        if release.get('name') == closest_match:
                            writer.writerow({
                                'Tech Name': tech_name,
                                'Application': product.get('application', ''),
                                'Name': product.get('name', ''),
                                'Description': product.get('description', ''),
                                'Manufacturer Name': product.get('manufacturer', {}).get('name', ''),
                                'Manufacturer Description': product.get('manufacturer', {}).get('description', ''),
                                'Release Name': release.get('name', ''),
                                'End of Life': release.get('softwareLifecycle', {}).get('endOfLife', ''),
                                'End of Life Support Level': release.get('softwareLifecycle', {}).get('endOfLifeSupportLevel', ''),
                                'Obsolete': release.get('softwareLifecycle', {}).get('obsolete', ''),
                                'Similarity': score
                            })
                            break
                    if release.get('name') == closest_match:
                        break
        else:
            print(Fore.RED + f"Tecnologia não encontrada: {tech_name}" + Fore.RESET)

if __name__ == "__main__":
    main()
