import json
import random
from datetime import datetime, timedelta
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update

# Seu Telegram ID admin
ADMIN_ID = 5052937721

# Arquivo para salvar dados (clientes e códigos)
DATA_FILE = "clientes.json"

# Dicionário para armazenar dados em runtime
dados = {
    "clientes": {},  # user_id : {"validade": "YYYY-MM-DDTHH:MM:SS"}
    "codigos": {}    # codigo : {"ativo": True/False, "gerado_em": "YYYY-MM-DDTHH:MM:SS"}
}

def salvar_dados():
    with open(DATA_FILE, "w") as f:
        json.dump(dados, f)

def carregar_dados():
    global dados
    try:
        with open(DATA_FILE, "r") as f:
            dados = json.load(f)
    except FileNotFoundError:
        salvar_dados()  # Cria arquivo vazio na primeira vez

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Olá! Use /gerarcodigo para gerar um código de ativação (somente admin).\n"
        "Clientes usam /ativar <codigo> para ativar seu acesso."
    )

def gerar_codigo(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        update.message.reply_text("Você não tem permissão para usar este comando.")
        return

    # Gera código único de 10 caracteres alfanuméricos
    while True:
        codigo = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))
        if codigo not in dados["codigos"]:
            break

    dados["codigos"][codigo] = {
        "ativo": True,
        "gerado_em": datetime.utcnow().isoformat()
    }
    salvar_dados()

    update.message.reply_text(f"Código gerado: {codigo}")

def ativar(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    args = context.args

    if user_id == str(ADMIN_ID):
        # Admin sempre liberado
        update.message.reply_text("Seu acesso é permanente e liberado automaticamente.")
        return

    if not args:
        update.message.reply_text("Use: /ativar <codigo>")
        return

    codigo = args[0].upper()
    if codigo not in dados["codigos"]:
        update.message.reply_text("Código inválido.")
        return

    if not dados["codigos"][codigo]["ativo"]:
        update.message.reply_text("Este código já foi usado.")
        return

    # Ativa para o usuário por 30 dias
    validade = datetime.utcnow() + timedelta(days=30)
    dados["clientes"][user_id] = {"validade": validade.isoformat()}

    # Marca código como usado
    dados["codigos"][codigo]["ativo"] = False
    salvar_dados()

    update.message.reply_text(f"Ativação feita com sucesso! Seu acesso é válido até {validade.strftime('%d/%m/%Y %H:%M:%S UTC')}.")

def check_acesso(user_id: int) -> bool:
    user_id_str = str(user_id)
    if user_id == ADMIN_ID:
        return True
    if user_id_str in dados["clientes"]:
        validade = datetime.fromisoformat(dados["clientes"][user_id_str]["validade"])
        if datetime.utcnow() <= validade:
            return True
        else:
            # Acesso expirou, remove cliente
            del dados["clientes"][user_id_str]
            salvar_dados()
    return False

# Exemplo de função que enviaria sinal após padrão (implementar conforme seu código original)
def enviar_sinal(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not check_acesso(user_id):
        update.message.reply_text("Você precisa ativar seu acesso usando /ativar <codigo> para receber sinais.")
        return
    # Aqui entra sua lógica para enviar sinal automaticamente
    update.message.reply_text("Sinal enviado! (lógica do padrão de 10 resultados)")

def main():
    carregar_dados()
    TOKEN = '7920202192:AAEGpjy5k39moDng2DpWqw_LEgmmFU-QI1U'
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("gerarcodigo", gerar_codigo))
    dp.add_handler(CommandHandler("ativar", ativar))
    # dp.add_handler(CommandHandler("sinal", enviar_sinal))  # Não necessário, sinais automáticos

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
