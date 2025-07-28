import json

def carregar_dados():
    with open('access.json', 'r') as f:
        dados = json.load(f)
        print("Bot iniciado com token:", dados['telegram_token'])

if __name__ == '__main__':
    carregar_dados()