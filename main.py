import logging
import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# IDs e dados
ADMIN_ID = 5052937721  # Seu ID permanente
users_data = {}
codes_validos = set()
codes_ativos = {}

# Ativação de logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Gerar códigos únicos
def gerar_codigo():
    letras = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choices(letras, k=8))

# Comando para o admin gerar códigos
async def gerar_codigo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Você não tem permissão para gerar códigos.")
        return
    codigo = gerar_codigo()
    codes_validos.add(codigo)
    await update.message.reply_text(f"✅ Código gerado: `{codigo}`", parse_mode="Markdown")

# Comando de ativação do código
async def ativar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Use o comando assim: /ativar <seu código>")
        return

    codigo = context.args[0].upper()
    user_id = update.effective_user.id

    if user_id == ADMIN_ID:
        users_data[user_id] = {'expira_em': datetime.max}
        await update.message.reply_text("✅ Acesso vitalício liberado para o administrador.")
        return

    if codigo not in codes_validos:
        await update.message.reply_text("❌ Código inválido ou já utilizado.")
        return

    expira_em = datetime.now() + timedelta(days=30)
    users_data[user_id] = {'expira_em': expira_em}
    codes_validos.remove(codigo)
    codes_ativos[codigo] = user_id

    await update.message.reply_text("✅ Código ativado com sucesso! Você pode começar a enviar sua sequência.")

# Verificação de acesso
def acesso_liberado(user_id):
    if user_id == ADMIN_ID:
        return True
    dados = users_data.get(user_id)
    if not dados:
        return False
    return dados['expira_em'] > datetime.now()

# Lógica de análise dos sinais
async def processar_sinal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = update.message.text.lower().strip()

    # Verifica acesso
    if not acesso_liberado(user_id):
        await update.message.reply_text("🚫 Você não tem acesso. Use /ativar <código> para liberar o sinal.")
        return

    # Filtrar apenas g e p
    sequencia = ''.join([c for c in texto if c in ['g', 'p']])

    if len(sequencia) != 10:
        await update.message.reply_text("⚠️ Envie exatamente 10 resultados usando apenas G ou P. Ex: `gpgppggpgp`", parse_mode="Markdown")
        return

    ultimos3 = sequencia[-3:]
    if ultimos3 == 'ggg' or ultimos3 == 'ppp':
        await update.message.reply_text("⚠️ Padrão não favorável detectado.\nPor segurança, aguarde mais 3 rodadas antes de voltar a apostar.")
        return

    g_count = sequencia.count('g')
    p_count = sequencia.count('p')

    if g_count == p_count:
        await update.message.reply_text("⚠️ Padrão não favorável detectado.\nPor segurança, aguarde mais 3 rodadas antes de voltar a apostar.")
        return

    sinal = 'P' if g_count > p_count else 'G'
    await update.message.reply_text(
        f"🎯 Próxima aposta: *{sinal}*\nUse no máximo 3 gales para otimizar suas chances.\nApós ganhar no green, aguarde 3 rodadas antes de apostar novamente.",
        parse_mode="Markdown"
    )

# Inicialização do bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Envie uma sequência de 10 resultados (G ou P) para receber seu sinal!")

# Main
if __name__ == '__main__':
    app = ApplicationBuilder().token("COLE_SEU_TOKEN_AQUI").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ativar", ativar_cmd))
    app.add_handler(CommandHandler("gerarcodigo", gerar_codigo_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_sinal))

    print("🤖 Bot iniciado...")
    app.run_polling()
