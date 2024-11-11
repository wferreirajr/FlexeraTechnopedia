import csv
import json
from fuzzywuzzy import process

# Carrega o arquivo CSV techs.csv
csv_file_path = "techs.csv"

# Lê o arquivo CSV e armazena as linhas em uma lista
with open(csv_file_path, mode='r') as file:
    reader = csv.reader(file, delimiter=',')
    next(reader)  # Pula o cabeçalho
    techs = [row for row in reader]

print(f"Arquivo CSV ({csv_file_path}) carregado com sucesso.")

# Carrega o arquivo JSON response.json
json_file_path = "response.json"

# Lê o arquivo JSON e armazena os dados em um dicionário
with open(json_file_path, mode='r') as file:
    data = json.load(file)

print(f"Arquivo JSON ({json_file_path}) carregado com sucesso.\n")

# Itera sobre as linhas do CSV e procura a tecnologia no JSON
for tech in techs:
    tech_name = tech[0]
    software_products = data.get('data', {}).get('SoftwareProduct', [])
    names = [release['name'] for product in software_products for release in product.get('softwareReleases', [])]
    result = process.extractOne(tech_name, names, score_cutoff=60)
    
    if result:
        closest_match, score = result
        print(f"Tecnologia encontrada: {tech_name}: {closest_match} (similaridade: {score}%)")
    else:
        print(f"Tecnologia não encontrada: {tech_name}")