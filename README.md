# FlexeraTechnopedia

Este projeto contém scripts para consultar a API Flexera e obter informações sobre o fim de vida de tecnologias. Ele inclui um script Python (`FlexeraQuery.py`) e um script Bash (`FlexeraQuery.sh`).

## Instalação

1. Clone o repositório:
    ```sh
    git clone https://github.com/wferreirajr/FlexeraTechnopedia.git
    cd FlexeraTechnopedia
    ```

2. Crie e ative um ambiente virtual:
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3. Instale as dependências:
    ```sh
    pip install -r requirements.txt
    ```

## Execução

### Script Python

Para executar o script Python, use o seguinte comando:

```sh
python FlexeraQuery.py --token TOKEN
```

### Script Bash

Para executar o script Bash, use o seguinte comando:

```sh
chmod +x FlexeraQuery.sh
./FlexeraQuery.sh TOKEN
```