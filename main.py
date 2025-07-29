import os
import random
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Obter token do ambiente
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Token do bot não definido na variável de ambiente BOT_TOKEN")

# Seu ID liberado (sem precisar de código)
ADMIN_ID = 5052937721

# Armazenamento simples na memória (substitua por DB se quiser persistência real)
clientes_ativos = {}  # user_id: validade (datetime)
codigos_ativos = {}   # codigo: validade (datetime)
usuarios_aguardando = set()  # IDs que devem aguardar 3 rodadas após ganho no green

def gerar_codigo_unico():
    while True:
        codigo = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))
        if codigo not in codigos_ativos:
            return codigo

def validar_codigo(codigo):
    validade = codigos_ativos.get(codigo)
    if validade and validade > datetime.datetime.now():
        return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Envie uma sequência de 10 resultados usando 'g' ou 'p' (exemplo: gpgppggpgp) para receber sinais.\n"
        "Comandos:\n"
        "/gerarcodigo - (admin) gera código de ativação\n"
        "/ativar <codigo> - ativa seu acesso por 30 dias\n"
    )

async def gerarcodigo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Você não tem permissão para usar este comando.")
        return
    codigo = gerar_codigo_unico()
    validade = datetime.datetime.now() + datetime.timedelta(days=30)
    codigos_ativos[codigo] = validade
    await update.message.reply_text(f"Código gerado: {codigo} - válido por 30 dias.")

async def ativar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        # Admin sempre liberado
        clientes_ativos[user_id] = datetime.datetime.max
        await update.message.reply_text("Admin liberado para usar o bot sem ativação.")
        return

    if not context.args:
        await update.message.reply_text("Use /ativar <codigo> para ativar seu acesso.")
        return

    codigo = context.args[0].upper()
    if validar_codigo(codigo):
        validade = codigos_ativos.pop(codigo)
        clientes_ativos[user_id] = validade
        await update.message.reply_text(f"Acesso ativado até {validade.strftime('%d/%m/%Y %H:%M:%S')}")
    else:
        await update.message.reply_text("Código inválido ou expirado.")

def limpar_entrada(texto: str) -> str:
    texto = texto.lower()
    return ''.join(c for c in texto if c in ['g', 'p'])

def analisar_sequencia(seq: str):
    # Últimos 3 iguais?
    ultimos3 = seq[-3:]
    if ultimos3 == 'ggg' or ultimos3 == 'ppp':
        return 'AGUARDAR'
    count_g = seq.count('g')
    count_p = seq.count('p')
    if count_g > count_p:
        return 'P'
    elif count_p > count_g:
        return 'G'
    else:
        return 'AGUARDAR'

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Verifica se usuário está ativo
    validade = clientes_ativos.get(user_id)
    if user_id != ADMIN_ID:
        if not validade or validade < datetime.datetime.now():
            await update.message.reply_text(
                "Você precisa ativar o bot com um código válido. Use /ativar <codigo> para ativar."
            )
            return

    texto = update.message.text
    seq = limpar_entrada(texto)

    if len(seq) != 10:
        await update.message.reply_text(
            "Por favor, envie exatamente 10 resultados com letras 'g' ou 'p', ex: gpgppggpgp"
        )
        return

    if user_id in usuarios_aguardando:
        await update.message.reply_text(
            "⚠️ Aguarde 3 rodadas antes de apostar novamente após um green."
        )
        return

    resultado = analisar_sequencia(seq)

    if resultado == 'AGUARDAR':
        await update.message.reply_text(
            "⚠️ Padrão não favorável detectado.\nPor segurança, aguarde mais 3 rodadas antes de voltar a apostar."
        )
        return

    # Envia sinal
    await update.message.reply_text(
        f"🎯 Próxima aposta: {resultado.upper()}\nUse no máximo 3 gales para otimizar suas chances.\n"
        "Após ganhar no green, aguarde 3 rodadas antes de apostar novamente."
    )

    # Adiciona usuário à lista de espera para 3 rodadas
    usuarios_aguardando.add(user_id)

    # Agendar remoção da espera em 3 rodadas (simplificado: após 3 mensagens recebidas do usuário)
    # Para simplificar, removemos após 3 mensagens do próprio usuário.
    # Pode ser adaptado para usar timers ou contador real.

    # Guardar contador no contexto
    if "contador_rodadas" not in context.user_data:
        context.user_data["contador_rodadas"] = 0
    context.user_data["contador_rodadas"] += 1
    if context.user_data["contador_rodadas"] >= 3:
        usuarios_aguardando.discard(user_id)
        context.user_data["contador_rodadas"] = 0
        await update.message.reply_text("✅ Você pode apostar novamente!")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gerarcodigo", gerarcodigo))
    app.add_handler(CommandHandler("ativar", ativar))

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), processar_mensagem))

    print("Bot rodando...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
