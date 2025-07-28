import json
import os
import logging
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

ACCESS_FILE = "access.json"

access_codes = {
    "leo202501": {"used": False, "expires": "2025-08-28"},
    "enrique202501": {"used": False, "expires": "2025-08-28"},
    "carlos20250825": {"used": False, "expires": "2025-08-25"},
    "joao20250915": {"used": False, "expires": "2025-09-15"},
    "acesso30": {"used": False, "expires": "2099-12-31"}
}

AUTHORIZED_USERS = {5052937721}

app = Flask('')

@app.route('/')
def home():
    return "Bot está rodando!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

def load_access():
    if not os.path.isfile(ACCESS_FILE):
        return {"users": {}, "codes": access_codes}
    with open(ACCESS_FILE, "r") as f:
        return json.load(f)

def save_access(data):
    with open(ACCESS_FILE, "w") as f:
        json.dump(data, f)

def check_access(user_id, access_data):
    if user_id in AUTHORIZED_USERS:
        return True
    users = access_data.get("users", {})
    if str(user_id) not in users:
        return False
    date_str = users[str(user_id)]["date"]
    ativation_date = datetime.strptime(date_str, "%Y-%m-%d")
    return datetime.now() - ativation_date <= timedelta(days=30)

def activate_user(user_id, code, access_data):
    users = access_data.get("users", {})
    codes = access_data.get("codes", access_codes)
    users[str(user_id)] = {"date": datetime.now().strftime("%Y-%m-%d"), "code": code}
    codes[code] = {"used": True, "expires": codes[code]["expires"]}
    access_data["users"] = users
    access_data["codes"] = codes
    save_access(access_data)

def start(update, context):
    try:
        user_id = update.effective_user.id
        access_data = load_access()
        if check_access(user_id, access_data):
            update.message.reply_text("Você já está autorizado!\nEnvie os últimos 10 resultados usando G e P.\nExemplo: gpgppggpgp")
        else:
            update.message.reply_text("Bem-vindo! Para usar o bot, envie seu código único usando o comando /ativar.\nExemplo: /ativar SEUCODIGO")
    except Exception as e:
        logging.error(f"Erro no start: {e}")

def ativar(update, context):
    try:
        user_id = update.effective_user.id
        access_data = load_access()
        codes = access_data.get("codes", access_codes)
        if len(context.args) != 1:
            update.message.reply_text("Use o comando assim: /ativar SEUCODIGO")
            return
        code = context.args[0].lower()
        if code not in codes:
            update.message.reply_text("Código inválido ou inexistente. Tente novamente.")
            return
        if codes[code]["used"]:
            update.message.reply_text("Esse código já foi usado. Solicite um código novo para renovar.")
            return
        activate_user(user_id, code, access_data)
        update.message.reply_text("Código aceito! Acesso liberado por 30 dias.\nAgora envie os últimos 10 resultados usando G e P.\nExemplo: gpgppggpgp")
    except Exception as e:
        logging.error(f"Erro no ativar: {e}")
        update.message.reply_text("Ocorreu um erro ao ativar. Tente novamente mais tarde.")

def process_results(update, text, user_id):
    try:
        access_data = load_access()
        if not check_access(user_id, access_data):
            update.message.reply_text("Seu acesso expirou ou não foi ativado.\nUse /ativar SEUCODIGO para renovar.")
            return
        cleaned = ''.join(c.lower() for c in text if c.lower() in ['g','p'])
        resultados = list(cleaned)
        if len(resultados) != 10:
            update.message.reply_text("Por favor, envie exatamente 10 resultados usando apenas as letras G e P, sem espaços ou vírgulas.\nExemplo: gpgppggpgp")
            return
        ultimos_3 = resultados[-3:]
        if ultimos_3[0] == ultimos_3[1] == ultimos_3[2]:
            msg = "⚠️ Padrão não favorável detectado.\nPor segurança, aguarde mais 3 rodadas antes de voltar a apostar."
        else:
            count_g = resultados.count("g")
            count_p = resultados.count("p")
            aposta = "p" if count_g > count_p else "g" if count_p > count_g else None
            msg = (f"🎯 Próxima aposta: {aposta.upper()}\nUse no máximo 3 gales para otimizar suas chances.\nApós ganhar no green, aguarde 3 rodadas antes de apostar novamente."
                   if aposta else "⚠️ Padrão não favorável detectado.\nPor segurança, aguarde mais 3 rodadas antes de voltar a apostar.")
        update.message.reply_text(msg)
    except Exception as e:
        logging.error(f"Erro no process_results: {e}")
        update.message.reply_text("Erro ao processar resultados. Tente novamente.")

def handle_message(update, context):
    try:
        user_id = update.effective_user.id
        text = update.message.text.strip()
        if text.startswith("/"):
            return
        process_results(update, text, user_id)
    except Exception as e:
        logging.error(f"Erro no handle_message: {e}")

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("ativar", ativar))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    keep_alive()
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
