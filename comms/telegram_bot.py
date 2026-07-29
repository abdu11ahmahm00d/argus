import io
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import structlog

log = structlog.get_logger()


class TelegramBot:
    def __init__(self, token: str, supervisor_id: int):
        self.token = token
        self.supervisor_id = supervisor_id
        self.app = Application.builder().token(token).build()
        self._heatmap_fn = None
        self._status_fn = None
        self._arm_fn = None
        self._disarm_fn = None
        self._register_handlers()
        log.info("telegram_bot_initialized")

    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("status", self._cmd_status))
        self.app.add_handler(CommandHandler("heatmap", self._cmd_heatmap))
        self.app.add_handler(CommandHandler("compliance", self._cmd_compliance))
        self.app.add_handler(CommandHandler("workers", self._cmd_workers))
        self.app.add_handler(CommandHandler("log", self._cmd_log))
        self.app.add_handler(CommandHandler("report", self._cmd_report))
        self.app.add_handler(CommandHandler("arm", self._cmd_arm))
        self.app.add_handler(CommandHandler("disarm", self._cmd_disarm))
        self.app.add_handler(CommandHandler("help", self._cmd_help))

    def register_heatmap_fn(self, fn):
        self._heatmap_fn = fn

    def register_status_fn(self, fn):
        self._status_fn = fn

    def register_arm_fn(self, fn):
        self._arm_fn = fn

    def register_disarm_fn(self, fn):
        self._disarm_fn = fn

    async def _check_supervisor(self, update: Update) -> bool:
        if update.effective_user.id != self.supervisor_id:
            await update.message.reply_text("⛔ Unauthorized")
            return False
        return True

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_supervisor(update):
            return
        await update.message.reply_text("🟢 ARGUS active.\nSend /help for commands.")

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_supervisor(update):
            return
        if self._status_fn:
            msg = await self._status_fn()
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("Status: unknown")

    async def _cmd_heatmap(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_supervisor(update):
            return
        if self._heatmap_fn:
            jpg_bytes = self._heatmap_fn()
            if jpg_bytes:
                photo = io.BytesIO(jpg_bytes)
                photo.name = "heatmap.jpg"
                await update.message.reply_photo(photo=photo)
            else:
                await update.message.reply_text("❌ Could not capture heatmap")
        else:
            await update.message.reply_text("Heatmap unavailable")

    async def _cmd_compliance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_supervisor(update):
            return
        await update.message.reply_text(
            "Compliance data not yet available this session."
        )

    async def _cmd_workers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_supervisor(update):
            return
        await update.message.reply_text("No workers currently tracked.")

    async def _cmd_log(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_supervisor(update):
            return
        await update.message.reply_text("Session log not available.")

    async def _cmd_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_supervisor(update):
            return
        await update.message.reply_text("Report generation not yet implemented.")

    async def _cmd_arm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_supervisor(update):
            return
        if self._arm_fn:
            await self._arm_fn()
        await update.message.reply_text("🟢 ARGUS armed.")

    async def _cmd_disarm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_supervisor(update):
            return
        if self._disarm_fn:
            await self._disarm_fn()
        await update.message.reply_text("⚫ ARGUS disarmed.")

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self._check_supervisor(update):
            return
        text = (
            "/status - Zone occupancy\n"
            "/heatmap - Annotated camera view\n"
            "/compliance - Helmet compliance %\n"
            "/workers - Tracked workers\n"
            "/log - Entry/exit timestamps\n"
            "/report - Full session summary\n"
            "/arm - Arm system\n"
            "/disarm - Disarm system\n"
            "/help - This message"
        )
        await update.message.reply_text(text)

    async def send_alert(self, message: str, photo_bytes: bytes | None = None):
        try:
            if photo_bytes:
                photo = io.BytesIO(photo_bytes)
                photo.name = "alert.jpg"
                await self.app.bot.send_photo(
                    chat_id=self.supervisor_id, photo=photo, caption=message
                )
            else:
                await self.app.bot.send_message(
                    chat_id=self.supervisor_id, text=message
                )
        except Exception as e:
            log.error("telegram_send_failed", error=str(e))

    async def start_polling(self):
        log.info("telegram_bot_starting")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

    async def stop(self):
        log.info("telegram_bot_stopping")
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
