import requests
import json
import csv
import os
import argparse
from fuzzywuzzy import process
from colorama import init, Fore

# Inicializa o colorama para saída colorida no terminal
init(autoreset=True)

def get_args():
    """
    Configura e processa os argumentos da linha de comando.
    
    Returns:
        argparse.Namespace: Objeto contendo os argumentos processados.
    """
    parser = argparse.ArgumentParser(description="Script para consultar a API Flexera.")
    parser.add_argument("--token", required=True, help="Token de atualização da API Flexera.")
    parser.add_argument("--OrgId", required=True, help="Número da OrgID para uso da API Flexera.")
    parser.add_argument("--InputFile", required=False, help="Nome da tecnologia a ser pesquisada.")
    parser.add_argument("--OutputFile", required=False, help="Nome do arquivo de saída.")
    return parser.parse_args()

args = get_args()
ORGANIZATION_ID = args.OrgId
CSV_FILE_PATH = args.InputFile if args.InputFile else "techs.csv"
OUTPUT_CSV_FILE = args.OutputFile if args.OutputFile else "output.csv"

def get_flexera_token(refresh_token, current_token=None):
    """
    Obtém ou atualiza o token de acesso da API Flexera.
    
    Args:
        refresh_token (str): Token de atualização para obter um novo token de acesso.
        current_token (str, optional): Token de acesso atual para verificar validade.
    
    Returns:
        str: Token de acesso válido.
    
    Raises:
        Exception: Se falhar ao obter um novo token.
    """
    if current_token:
        # Verifica se o token atual ainda é válido
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

    # Obtém um novo token
    url = "https://login.flexera.com/oidc/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        new_token = response.json().get("access_token")
        print("Novo token gerado.")
        return new_token
    raise Exception(f"Falha ao obter o token com código de status {response.status_code}: {response.text}")

def get_product(software_product_name, token):
    """
    Obtém informações do produto de software da API Flexera.
    
    Args:
        software_product_name (str): Nome do produto de software.
        token (str): Token de acesso para a API Flexera.
    
    Returns:
        str: Caminho do arquivo JSON com as informações do produto, ou None se falhar.
    """
    if not os.path.exists("output_json"):
        os.makedirs("output_json")

    check_filename = os.path.join("output_json",f"output_{software_product_name}.json")
    if os.path.exists(check_filename):
        return check_filename

    url = f"https://api.flexera.com/content/v2/orgs/{ORGANIZATION_ID}/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    query = json.dumps({ 
        "query": f"""
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
    })

    query1 = json.dumps({ 
        "query": f"""
        query SoftwareProductList {{
            Manufacturer(name: "{software_product_name}") {{
                name
                softwareProducts {{
                    name
                }}
            }}
        }}
        """
    })

    query2 = json.dumps({ 
        "query": f"""
        query SoftwareProductList {{
            SoftwareRelease(application: "{software_product_name}") {{
                name
                application
            }}
        }}
        """
    })

    response = requests.post(url, headers=headers, data=query)
    if response.status_code == 200:
        data = response.json()
        with open(check_filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        return check_filename
    print(f"A consulta falhou com o código de status {response.status_code}: {response.text}")
    return None

def main():
    """
    Função principal que executa o fluxo do script.
    """
    args = get_args()
    token = get_flexera_token(args.token)
    
    try:
        # Carrega as tecnologias únicas do arquivo CSV
        unique_techs = set()
        techs = []

        with open(CSV_FILE_PATH, mode='r') as file:
            reader = csv.reader(file, delimiter=';')
            next(reader)  # Pula o cabeçalho
            for row in reader:
                tech_name = row[0]
                if tech_name not in unique_techs:
                    unique_techs.add(tech_name)
                    techs.append(row)
        
        print(f"Arquivo CSV ({CSV_FILE_PATH}) carregado com sucesso. {len(techs)} techs únicas encontradas.")
    except FileNotFoundError:
        print(f"Arquivo CSV ({CSV_FILE_PATH}) não encontrado.")

    for tech in techs:
        tech_name = tech[0]
        # Remove caracteres não alfanuméricos do nome da tecnologia
        #tech_name = ''.join(e if e.isalnum() or e.isspace() else ' ' for e in tech_name)

        json_file_path = get_product(tech_name, token)
        if not json_file_path:
            continue

        with open(json_file_path, mode='r') as file:
            data = json.load(file)

        software_products = data.get('data', {}).get('SoftwareProduct', [])
        if not software_products:
            print(Fore.RED + f"O retorno da tech ({tech_name}) foi vazio." + Fore.RESET)
            continue

        # Extrai os nomes das versões de software
        names = [release['name'] for product in software_products for release in product.get('softwareReleases', [])]
        # Encontra a correspondência mais próxima usando fuzzy matching
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
