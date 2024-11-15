#!/bin/bash

# Chamada via curl
# curl https://api.flexera.com/content/v2/orgs/XXXXX/graphql -H "Authorization: Bearer $TOKEN" -d '{"query": "query SoftwareProductList {Manufacturer(name: \"Microsoft\") {id  name softwareProducts {id name }}\n}"}'

# Verifica se o parâmetro foi passado
if [ -z "$1" ]; then
    echo "Uso: $0 <token>"
    exit 1
fi

# Atribui o parâmetro à variável token
token=$1

#!/bin/bash

ORGANIZATION_ID="XXXXX"

get_flexera_token() {
    local refresh_token=$1
    local current_token=$2

    if [ -n "$current_token" ]; then
        local url="https://api.flexera.com/content/v2/orgs/${ORGANIZATION_ID}/graphql"
        local headers="Authorization: Bearer $current_token"
        local data='{"query": "{ __typename }"}'
        local response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$url" -H "$headers" -H "Content-Type: application/json" -d "$data")

        if [ "$response" -eq 200 ]; then
            echo "O token atual ainda é válido."
            echo "$current_token"
            return
        fi
        echo "O token atual está expirado, gerando um novo token."
    fi

    local url="https://login.flexera.com/oidc/token"
    local headers="Content-Type: application/x-www-form-urlencoded"
    local data="grant_type=refresh_token&refresh_token=$refresh_token"
    local response=$(curl -s -X POST "$url" -H "$headers" -d "$data")
    local status_code=$(echo "$response" | jq -r '.status_code // 0')

    if [ "$status_code" -eq 0 ]; then
        local new_token=$(echo "$response" | jq -r '.access_token')
        if [ "$new_token" != "null" ]; then
            #echo "Novo token gerado."
            echo "$new_token"
        else
            local error_message=$(echo "$response" | jq -r '.error_description')
            #echo "Falha ao obter o token: $error_message"
            exit 1
        fi
    else
        local error_message=$(echo "$response" | jq -r '.error_description')
        #echo "Falha ao obter o token com código de status $status_code: $error_message"
        exit 1
    fi
}

# Exemplo de uso da função
refresh_token=$token
current_token=$(get_flexera_token "$refresh_token")
#echo $current_token

produto="CentOS"
url="https://api.flexera.com/content/v2/orgs/${ORGANIZATION_ID}/graphql"
headers="Authorization: Bearer $current_token"
data='{"query": "query SoftwareProductList { Manufacturer(name: \"'$produto'\") { id name softwareProducts { id name } } }"}'

response=$(curl -s -X POST "$url" -H "$headers" -H "Content-Type: application/json" -d "$data")
echo "Resposta da consulta: $response"
