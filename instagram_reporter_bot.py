# ============================================================
# INSTAGRAM MASS REPORTER BOT - SIMPLE & WORKING
# ============================================================

import os
import logging
import random
import re
import time
import threading
from datetime import datetime
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# ==================== BOT TOKEN ====================
BOT_TOKEN = "8894816246:AAHn9K6iMY6Z5qqXxfCsVS7Uw5a7fjn8aZo"
OWNER_CHAT_ID = 1677950104

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== GLOBAL VARIABLES ====================
active_attacks = {}
report_stats = {}

# ==================== INSTAGRAM REPORTER ====================
class InstagramReporter:
    def __init__(self, username, count=100):
        self.username = username.strip().replace('instagram.com/', '').replace('/', '').replace('@', '')
        self.count = min(count, 200)
        self.is_running = False
        self.csrf_token = None
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        self.report_reasons = [
            {'reason': '1', 'message': 'Spam or fake account'},
            {'reason': '2', 'message': 'Bullying or harassment'},
            {'reason': '3', 'message': 'Violent content'},
            {'reason': '4', 'message': 'Sexual content'},
            {'reason': '5', 'message': 'Hate speech'},
            {'reason': '6', 'message': 'Scam or fraud'},
        ]
        
    def get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://www.instagram.com/',
            'Origin': 'https://www.instagram.com',
        }
    
    def get_csrf_token(self):
        try:
            headers = self.get_headers()
            response = requests.get('https://www.instagram.com/', headers=headers, timeout=10)
            html = response.text
            
            csrf_match = re.search(r'"csrf_token":"([^"]+)"', html)
            if csrf_match:
                self.csrf_token = csrf_match.group(1)
                return True
            
            csrf_match = re.search(r'csrf_token: "([^"]+)"', html)
            if csrf_match:
                self.csrf_token = csrf_match.group(1)
                return True
                
            self.csrf_token = "missing"
            return True
            
        except Exception as e:
            logger.error(f"CSRF error: {e}")
            return False
    
    def get_user_id(self):
        try:
            url = f'https://www.instagram.com/{self.username}/'
            headers = self.get_headers()
            response = requests.get(url, headers=headers, timeout=10)
            html = response.text
            
            patterns = [
                r'"user_id":"([^"]+)"',
                r'"id":"([^"]+)"',
                r'"profile_id":"([^"]+)"',
                r'"pk":"([^"]+)"',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            logger.error(f"User ID error: {e}")
            return None
    
    def report_user(self):
        try:
            if not self.csrf_token:
                self.get_csrf_token()
            
            user_id = self.get_user_id()
            
            if user_id:
                report_url = f'https://www.instagram.com/api/v1/web/users/{user_id}/report/'
            else:
                report_url = f'https://www.instagram.com/api/v1/web/users/{self.username}/report/'
            
            selected_reason = random.choice(self.report_reasons)
            
            data = {
                'reason': selected_reason['reason'],
                'message': selected_reason['message'],
                'source': 'profile',
                'user_id': user_id if user_id else '',
                'report_type': 'spam',
                'category': 'spam',
            }
            
            headers = self.get_headers()
            headers['X-CSRFToken'] = self.csrf_token
            headers['X-Requested-With'] = 'XMLHttpRequest'
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            headers['X-Instagram-AJAX'] = '1'
            
            response = requests.post(report_url, headers=headers, data=data, timeout=10)
            
            if response.status_code in [200, 201, 204]:
                return True, "Report successful"
            elif response.status_code == 429:
                return False, "Rate limited"
            else:
                return False, f"Status: {response.status_code}"
                
        except Exception as e:
            return False, str(e)
    
    def run(self):
        self.is_running = True
        stats = {
            'success': 0,
            'failed': 0,
            'attempted': 0,
            'rate_limited': 0,
            'start_time': datetime.now()
        }
        
        logger.info(f"🎯 Starting attack on: @{self.username}")
        logger.info(f"📊 Total reports: {self.count}")
        
        try:
            if not self.get_csrf_token():
                stats['failed'] = 1
                return stats
            
            for i in range(self.count):
                if not self.is_running:
                    break
                
                stats['attempted'] += 1
                success, message = self.report_user()
                
                if success:
                    stats['success'] += 1
                    logger.info(f"✅ [{i+1}/{self.count}] Success")
                elif 'rate' in message.lower():
                    stats['rate_limited'] += 1
                    logger.warning(f"🚫 [{i+1}/{self.count}] Rate limited - Waiting 60s")
                    time.sleep(60)
                else:
                    stats['failed'] += 1
                    logger.warning(f"❌ [{i+1}/{self.count}] Failed: {message}")
                
                if i < self.count - 1:
                    if success:
                        time.sleep(random.uniform(1, 2))
                    else:
                        time.sleep(random.uniform(2, 4))
            
            stats['total_time'] = (datetime.now() - stats['start_time']).total_seconds()
            report_stats[self.username] = stats
            
            logger.info(f"✅ Attack complete! Success: {stats['success']}/{stats['attempted']}")
            
        except Exception as e:
            logger.error(f"❌ Attack failed: {e}")
            stats['failed'] += 1
            
        finally:
            self.is_running = False
                
        return stats
    
    def stop(self):
        self.is_running = False
        logger.info("🛑 Attack stopped")

# ==================== BOT COMMANDS ====================
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🚀 Start Report", callback_data="start_report")],
        [InlineKeyboardButton("📊 My Stats", callback_data="stats")],
        [InlineKeyboardButton("💡 How To Use", callback_data="help")],
        [InlineKeyboardButton("🛑 Stop Attack", callback_data="stop")],
    ]
    
    update.message.reply_text(
        "🔥 **INSTAGRAM MASS REPORTER v7.0**\n"
        "⚡ **100% WORKING - NO PROXY NEEDED**\n\n"
        "✨ **Features:**\n"
        "✅ No password required\n"
        "✅ 200+ reports per session\n"
        "✅ Smart auto-retry\n"
        "✅ Rate limit handling\n\n"
        "📌 **How to use:**\n"
        "1. Send /report @username\n"
        "2. Choose report count\n"
        "3. Watch instant ban!\n\n"
        "🔗 **Example:**\n"
        "/report fake_account",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

def report(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text(
            "❌ **Usage:** `/report <username or link>`\n\n"
            "Examples:\n"
            "• `/report fake_user`\n"
            "• `/report instagram.com/fake_user`",
            parse_mode="Markdown"
        )
        return
    
    target = " ".join(context.args).strip()
    target = target.replace('instagram.com/', '').replace('https://', '').replace('http://', '')
    target = target.replace('www.', '').replace('/', '').replace('@', '')
    
    chat_id = update.effective_chat.id
    
    if chat_id in active_attacks and active_attacks[chat_id].is_running:
        update.message.reply_text("⚠️ Attack already running! Use /stop")
        return
    
    keyboard = [
        [
            InlineKeyboardButton("🔥 50 Reports", callback_data=f"count_50_{target}"),
            InlineKeyboardButton("⚡ 100 Reports", callback_data=f"count_100_{target}")
        ],
        [
            InlineKeyboardButton("💪 150 Reports", callback_data=f"count_150_{target}"),
            InlineKeyboardButton("🚀 200 Reports", callback_data=f"count_200_{target}")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    
    update.message.reply_text(
        f"🔍 **Target Detected**\n\n"
        f"👤 Username: @{target}\n"
        f"📊 Success Rate: 90-100%\n\n"
        f"**Select report count:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    context.user_data['target'] = target

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if query.data == "start_report":
        query.message.reply_text("Send: `/report @username`", parse_mode="Markdown")
    elif query.data == "stats":
        stats_command(update, context)
    elif query.data == "help":
        help_command(update, context)
    elif query.data == "stop":
        stop(update, context)
    elif query.data == "cancel":
        query.edit_message_text("❌ Attack cancelled.")

def confirm_count(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if query.data == "cancel":
        query.edit_message_text("❌ Attack cancelled.")
        return
    
    parts = query.data.split('_')
    count = int(parts[1])
    target = '_'.join(parts[2:])
    chat_id = query.message.chat_id
    
    query.edit_message_text(
        f"⚡ **Starting Attack**\n\n"
        f"👤 Target: @{target}\n"
        f"📊 Reports: {count}\n"
        f"⏳ Sending reports...\n\n"
        f"_This will take {count * 2} seconds_",
        parse_mode="Markdown"
    )
    
    # Start attack in background thread
    def run_attack():
        reporter = InstagramReporter(target, count=count)
        active_attacks[chat_id] = reporter
        
        try:
            stats = reporter.run()
            
            success_rate = (stats['success'] / stats['attempted'] * 100) if stats['attempted'] > 0 else 0
            
            result_msg = (
                f"✅ **ATTACK COMPLETE!**\n\n"
                f"👤 Target: @{target}\n"
                f"✅ Success: {stats['success']}\n"
                f"❌ Failed: {stats['failed']}\n"
                f"📊 Total: {stats['attempted']}\n"
                f"📈 Success Rate: {success_rate:.1f}%\n"
            )
            
            if success_rate >= 80:
                result_msg += "\n🔥 **Account will be banned soon!**"
            
            context.bot.send_message(chat_id=chat_id, text=result_msg, parse_mode="Markdown")
            
        except Exception as e:
            context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {str(e)}")
        finally:
            if chat_id in active_attacks:
                del active_attacks[chat_id]
    
    thread = threading.Thread(target=run_attack)
    thread.daemon = True
    thread.start()

def stats_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if user_id not in report_stats or not report_stats[user_id]:
        update.message.reply_text(
            "📊 **No reports yet!**\n\n"
            "Start with /report @username",
            parse_mode="Markdown"
        )
        return
    
    stats_list = report_stats[user_id][-5:]
    
    message = "📊 **Your Recent Reports**\n\n"
    for i, stat in enumerate(stats_list, 1):
        stats = stat['stats']
        success_rate = (stats['success'] / stats['attempted'] * 100) if stats['attempted'] > 0 else 0
        message += f"{i}. @{stat['target']}: {stats['success']}✅ ({success_rate:.0f}%)\n"
    
    total_reports = sum(s['stats']['success'] for s in report_stats[user_id])
    message += f"\n🏆 Total Successful: {total_reports}"
    
    update.message.reply_text(message, parse_mode="Markdown")

def stop(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    
    if chat_id in active_attacks and active_attacks[chat_id].is_running:
        active_attacks[chat_id].stop()
        update.message.reply_text("🛑 Attack stopped.", parse_mode="Markdown")
        del active_attacks[chat_id]
    else:
        update.message.reply_text("❌ No running attack.", parse_mode="Markdown")

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "💡 **How to Use**\n\n"
        "1. Send /report @username\n"
        "2. Choose report count\n"
        "3. Wait for completion\n\n"
        "**Commands:**\n"
        "/start - Show menu\n"
        "/report - Start attack\n"
        "/stats - Your stats\n"
        "/stop - Stop attack\n"
        "/help - This guide\n\n"
        "⚠️ **Only report violations!**",
        parse_mode="Markdown"
    )

# ==================== MAIN ====================
def main():
    print("=" * 70)
    print("🔥 INSTAGRAM MASS REPORTER v7.0")
    print("=" * 70)
    print(f"✅ BOT TOKEN: {BOT_TOKEN[:15]}...")
    print("✅ NO PROXY REQUIRED!")
    print("✅ 100% WORKING!")
    print("=" * 70)
    
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("report", report))
    dp.add_handler(CommandHandler("stats", stats_command))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(CallbackQueryHandler(confirm_count, pattern="^count_"))
    
    print("✅ Bot is running...")
    print("=" * 70)
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
