from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update
import random
import json
import os
from datetime import datetime, timedelta

ADMIN_ID = 5052937721
CODES_FILE = "codes.json"
CLIENTS_FILE = "clients.json"
VALID_DAYS = 7

def load_data(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Olá! Use /gerarcodigo (admin) para criar código, /ativar <código> para ativar, /status para ver seu status."
    )

def gerar_codigo(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        update.message.reply_text("Você não tem permissão para usar este comando.")
        return
    
    codes = load_data(CODES_FILE)
    while True:
        codigo = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))
        if codigo not in codes:
            break
    
    expire_date = (datetime.now() + timedelta(days=VALID_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    codes[codigo] = {"used": False, "expire": expire_date}
    save_data(CODES_FILE, codes)

    update.message.reply_text(f"Código gerado: {codigo}\nVálido até: {expire_date}")

def ativar(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    args = context.args
    if len(args) != 1:
        update.message.reply_text("Use /ativar <código> para ativar.")
        return
    
    codigo = args[0].upper()
    codes = load_data(CODES_FILE)
    clients = load_data(CLIENTS_FILE)

    if codigo not in codes:
        update.message.reply_text("Código inválido.")
        return
    
    code_data = codes[codigo]
    if code_data["used"]:
        update.message.reply_text("Este código já foi usado.")
        return
    
    expire = datetime.strptime(code_data["expire"], "%Y-%m-%d %H:%M:%S")
    if datetime.now() > expire:
        update.message.reply_text("Este código está expirado.")
        return

    clients[user_id] = {
        "codigo": codigo,
        "ativado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expira_em": code_data["expire"]
    }
    save_data(CLIENTS_FILE, clients)

    codes[codigo]["used"] = True
    save_data(CODES_FILE, codes)

    update.message.reply_text(f"Ativado com sucesso! Seu acesso expira em {code_data['expire']}")

def status(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    clients = load_data(CLIENTS_FILE)
    if user_id not in clients:
        update.message.reply_text("Você não está ativado. Use /ativar <código> para ativar seu acesso.")
        return
    
    data = clients[user_id]
    expire = datetime.strptime(data["expira_em"], "%Y-%m-%d %H:%M:%S")
    agora = datetime.now()
    if agora > expire:
        update.message.reply_text("Seu acesso expirou. Por favor, ative novamente com um código válido.")
        return
    
    dias_restantes = (expire - agora).days
    update.message.reply_text(
        f"Você está ativado!\nCódigo usado: {data['codigo']}\nExpira em: {data['expira_em']} ({dias_restantes} dias restantes)"
    )

def main():
    TOKEN = "7920202192:AAEGpjy5k39moDng2DpWqw_LEgmmFU-QI1U"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("gerarcodigo", gerar_codigo))
    dp.add_handler(CommandHandler("ativar", ativar))
    dp.add_handler(CommandHandler("status", status))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
