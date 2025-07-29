from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import datetime
import random
import logging

# Configuração básica de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

ADMIN_ID = 5052937721
clients = {}
activation_codes = {}

def gerar_codigo_unico():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))

async def gerarcodigo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Você não tem permissão para usar este comando.")
        return
    codigo = gerar_codigo_unico()
    activation_codes[codigo] = datetime.datetime.now() + datetime.timedelta(days=30)
    await update.message.reply_text(f"Código gerado: {codigo}")

async def ativar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) != 1:
        await update.message.reply_text("Uso correto: /ativar <código>")
        return
    codigo = context.args[0].upper()
    if codigo in activation_codes:
        validade = activation_codes[codigo]
        if validade > datetime.datetime.now():
            clients[user_id] = validade
            del activation_codes[codigo]
            await update.message.reply_text(f"Código ativado com sucesso! Validade até {validade}.")
        else:
            await update.message.reply_text("Código expirado.")
    else:
        await update.message.reply_text("Código inválido.")

def cliente_ativo(user_id):
    if user_id == ADMIN_ID:
        return True
    validade = clients.get(user_id)
    if validade and validade > datetime.datetime.now():
        return True
    return False

async def analisar_resultado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not cliente_ativo(user_id):
        await update.message.reply_text("Você não está ativado. Use /ativar <código> para ativar seu acesso.")
        return
    if not context.args or len(context.args[0]) != 10:
        await update.message.reply_text("Envie uma sequência de 10 resultados (g/p), exemplo: /sinal gpgppggpgp")
        return
    seq = context.args[0].lower()
    seq = ''.join([c for c in seq if c in ['g', 'p']])
    if len(seq) != 10:
        await update.message.reply_text("Sequência inválida. Use somente 10 letras g ou p, juntas.")
        return
    if seq[-3:] == 'ggg' or seq[-3:] == 'ppp':
        await update.message.reply_text(
            "⚠️ Padrão não favorável detectado.\nPor segurança, aguarde mais 3 rodadas antes de apostar."
        )
        return
    g_count = seq.count('g')
    p_count = seq.count('p')
    if g_count > p_count:
        sinal = 'P'
    elif p_count > g_count:
        sinal = 'G'
    else:
        await update.message.reply_text(
            "⚠️ Padrão não favorável detectado.\nPor segurança, aguarde mais 3 rodadas antes de apostar."
        )
        return
    await update.message.reply_text(
        f"🎯 Próxima aposta: {sinal}\nUse no máximo 3 gales para otimizar suas chances.\nApós ganhar, aguarde 3 rodadas antes de apostar novamente."
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bem-vindo ao bot Wingo Arqueiro!\nUse /gerarcodigo (admin) para gerar códigos.\nClientes: use /ativar <código> para ativar.\n"
        "Para receber sinal, envie: /sinal <sequência de 10 resultados g/p>"
    )

def main():
    token = '7920202192:AAEGpjy5k39moDng2DpWqw_LEgmmFU-QI1U'
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gerarcodigo", gerarcodigo))
    app.add_handler(CommandHandler("ativar", ativar))
    app.add_handler(CommandHandler("sinal", analisar_resultado))

    logger.info("Bot rodando...")
    try:
        app.run_polling()
    except Exception as e:
        logger.error(f"Erro crítico no bot: {e}")

if __name__ == "__main__":
    main()
