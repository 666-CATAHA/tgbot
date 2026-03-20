import pyotp
import qrcode
import io
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = '8401975638:AAEKpZzaV7eJdGYEIqcStvljhNpVZpjgMiA'

# В реальном проекте храните это в базе данных!
user_secrets = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # 1. Генерируем уникальный секрет для пользователя
    secret = pyotp.random_base32()
    user_secrets[user_id] = secret
    
    # 2. Создаем URI для QR-кода (как в Госуслугах/Google Auth)
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=update.effective_user.username or "User", 
        issuer_name="TOTPTesterBot"
    )
    
    # 3. Генерируем картинку QR-кода
    qr = qrcode.make(otp_uri)
    img_byte_arr = io.BytesIO()
    qr.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    await update.message.reply_photo(
        photo=img_byte_arr,
        caption="1. Отсканируйте этот QR-код в приложении (Google Authenticator).\n"
                "2. Введите 6-значный код из приложения для проверки."
    )

async def verify_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_code = update.message.text
    
    if user_id not in user_secrets:
        await update.message.reply_text("Сначала введите команду /start")
        return

    # 4. Проверка кода
    totp = pyotp.TOTP(user_secrets[user_id])
    if totp.verify(user_code):
        await update.message.reply_text("✅ Код верный! Доступ разрешен.")
    else:
        await update.message.reply_text("❌ Код неверный. Попробуйте еще раз.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, verify_code))
    print("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()
