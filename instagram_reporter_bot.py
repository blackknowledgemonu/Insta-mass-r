# ============================================================
# INSTAGRAM MASS REPORTER - SUPER SIMPLE VERSION
# NO COMPLEX LIBRARIES - 100% WORKING
# ============================================================

import logging
import random
import re
import time
import threading
from datetime import datetime
import requests

# Use older telegram library version
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# ==================== BOT TOKEN ====================
BOT_TOKEN = "8894816246:AAHn9K6iMY6Z5qqXxfCsVS7Uw5a7fjn8aZo"
OWNER_CHAT_ID = 1677950104

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== GLOBAL ====================
active_attacks = {}
user_stats = {}

# ==================== SIMPLE INSTAGRAM REPORTER ====================
class SimpleInstagramReporter:
    def __init__(self, username, count=100):
        self.username = username.strip().replace('instagram.com/', '').replace('/', '').replace('@', '')
        self.count = min(count, 200)
        self.is_running = False
        self.csrf_token = None
        self.session = requests.Session()
        
        # Random user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        # Report reasons
        self.reasons = [
            'Spam or fake account',
            'Bullying or harassment',
            'Violent content',
            'Sexual content',
            'Hate speech',
            'Scam or fraud',
            'Impersonation'
        ]
    
    def _get_headers(self, csrf_token=None):
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://www.instagram.com/',
            'Origin': 'https://www.instagram.com',
        }
        if csrf_token:
            headers['X-CSRFToken'] = csrf_token
            headers['X-Requested-With'] = 'XMLHttpRequest'
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            headers['X-Instagram-AJAX'] = '1'
        return headers
    
    def _get_csrf_token(self):
        try:
            response = self.session.get('https://www.instagram.com/', headers=self._get_headers(), timeout=10)
            html = response.text
            
            # Try multiple patterns
            patterns = [
                r'"csrf_token":"([^"]+)"',
                r'csrf_token: "([^"]+)"',
                r'"csrfToken":"([^"]+)"',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    self.csrf_token = match.group(1)
                    return True
            
            # If no token found, try to get from cookies
            for cookie in self.session.cookies:
                if 'csrftoken' in cookie.name.lower():
                    self.csrf_token = cookie.value
                    return True
            
            self.csrf_token = None
            return False
            
        except Exception as e:
            logger.error(f"CSRF error: {e}")
            return False
    
    def _get_user_id(self):
        try:
            url = f'https://www.instagram.com/{self.username}/'
            response = self.session.get(url, headers=self._get_headers(), timeout=10)
            html = response.text
            
            # Try multiple patterns
            patterns = [
                r'"user_id":"([^"]+)"',
                r'"id":"([^"]+)"',
                r'"profile_id":"([^"]+)"',
                r'"pk":"([^"]+)"',
                r'"user_pk":"([^"]+)"',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    return match.group(1)
            
            # Try to get from JSON data
            json_match = re.search(r'window._sharedData = (.*?);</script>', html)
            if json_match:
                try:
                    import json
                    data = json.loads(json_match.group(1))
                    user_id = data.get('entry_data', {}).get('ProfilePage', [{}])[0].get('graphql', {}).get('user', {}).get('id')
                    if user_id:
                        return user_id
                except:
                    pass
            
            return None
            
        except Exception as e:
            logger.error(f"User ID error: {e}")
            return None
    
    def _send_report(self):
        try:
            if not self.csrf_token:
                self._get_csrf_token()
            
            if not self.csrf_token:
                return False, "No CSRF token"
            
            user_id = self._get_user_id()
            
            if user_id:
                report_url = f'https://www.instagram.com/api/v1/web/users/{user_id}/report/'
            else:
                report_url = f'https://www.instagram.com/api/v1/web/users/{self.username}/report/'
            
            # Random reason and message
            reason_msg = random.choice(self.reasons)
            reason_codes = ['1', '2', '3', '4', '5', '6', '7']
            
            data = {
                'reason': random.choice(reason_codes),
                'message': reason_msg,
                'source': 'profile',
                'user_id': user_id if user_id else '',
                'report_type': 'spam',
                'category': 'spam',
            }
            
            headers = self._get_headers(self.csrf_token)
            response = self.session.post(report_url, headers=headers, data=data, timeout=15)
            
            if response.status_code in [200, 201, 204, 202]:
                return True, "Report sent"
            elif response.status_code == 429:
                return False, "Rate limited"
            elif response.status_code == 403:
                return False, "Access denied"
            else:
                return False, f"Status {response.status_code}"
                
        except requests.Timeout:
            return False, "Timeout"
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
        
        logger.info(f"🎯 Starting on: @{self.username}")
        logger.info(f"📊 Total: {self.count}")
        
        try:
            # Get CSRF token first
            self._get_csrf_token()
            
            if not self.csrf_token:
                logger.warning("⚠️ Could not get CSRF token, trying anyway...")
            
            for i in range(self.count):
                if not self.is_running:
                    break
                
                stats['attempted'] += 1
                success, message = self._send_report()
                
                if success:
                    stats['success'] += 1
                    logger.info(f"✅ [{i+1}/{self.count}] Success")
                    time.sleep(random.uniform(1, 2))
                elif 'rate' in message.lower():
                    stats['rate_limited'] += 1
                    logger.warning(f"🚫 Rate limited - waiting 60s")
                    time.sleep(60)
                else:
                    stats['failed'] += 1
                    logger.warning(f"❌ [{i+1}/{self.count}] Failed: {message}")
                    time.sleep(random.uniform(2, 4))
            
            stats['total_time'] = (datetime.now() - stats['start_time']).total_seconds()
            
            # Save stats
            if self.username not in user_stats:
                user_stats[self.username] = []
            user_stats[self.username].append(stats)
            
            logger.info(f"✅ Complete! Success: {stats['success']}/{stats['attempted']}")
            
        except Exception as e:
            logger.error(f"❌ Attack failed: {e}")
            stats['failed'] += 1
            
        finally:
            self.is_running = False
            self.session.close()
        
        return stats
    
    def stop(self):
        self.is_running = False
        logger.info("🛑 Stopped")

# ==================== BOT COMMANDS ====================
def start(update, context):
    keyboard = [
        [InlineKeyboardButton("🚀 Start Report", callback_data="report")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("🛑 Stop", callback_data="stop")],
        [InlineKeyboardButton("💡 Help", callback_data="help")],
    ]
    
    update.message.reply_text(
        "🔥 **INSTAGRAM MASS REPORTER**\n\n"
        "Send /report @username\n\n"
        "Example: /report fake_account",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

def report(update, context):
    if not context.args:
        update.message.reply_text("❌ Usage: /report @username")
        return
    
    target = " ".join(context.args).strip()
    target = target.replace('instagram.com/', '').replace('https://', '').replace('http://', '')
    target = target.replace('www.', '').replace('/', '').replace('@', '')
    
    chat_id = update.effective_chat.id
    
    if chat_id in active_attacks and active_attacks[chat_id].is_running:
        update.message.reply_text("⚠️ Attack already running! Use /stop")
        return
    
    keyboard = [
        [InlineKeyboardButton("50", callback_data=f"50_{target}")],
        [InlineKeyboardButton("100", callback_data=f"100_{target}")],
        [InlineKeyboardButton("150", callback_data=f"150_{target}")],
        [InlineKeyboardButton("200", callback_data=f"200_{target}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ]
    
    update.message.reply_text(
        f"🎯 **Target:** @{target}\n\nSelect report count:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    context.user_data['target'] = target

def button_handler(update, context):
    query = update.callback_query
    query.answer()
    
    data = query.data
    
    if data == "cancel":
        query.edit_message_text("❌ Cancelled")
        return
    
    if data == "stop":
        chat_id = query.message.chat_id
        if chat_id in active_attacks:
            active_attacks[chat_id].stop()
            query.edit_message_text("🛑 Stopped")
            del active_attacks[chat_id]
        else:
            query.edit_message_text("❌ No running attack")
        return
    
    if data == "report":
        query.message.reply_text("Send: /report @username")
        return
    
    if data == "stats":
        stats_command(update, context)
        return
    
    if data == "help":
        help_command(update, context)
        return
    
    # Start attack
    parts = data.split('_')
    if len(parts) >= 2:
        count = int(parts[0])
        target = '_'.join(parts[1:])
        chat_id = query.message.chat_id
        
        query.edit_message_text(
            f"⚡ **Starting {count} reports on @{target}**\n\n"
            f"⏳ Please wait..."
        )
        
        def run_attack():
            reporter = SimpleInstagramReporter(target, count=count)
            active_attacks[chat_id] = reporter
            
            try:
                stats = reporter.run()
                
                success_rate = (stats['success'] / stats['attempted'] * 100) if stats['attempted'] > 0 else 0
                
                result = (
                    f"✅ **Attack Complete!**\n\n"
                    f"👤 @{target}\n"
                    f"✅ Success: {stats['success']}\n"
                    f"❌ Failed: {stats['failed']}\n"
                    f"🚫 Rate Limited: {stats['rate_limited']}\n"
                    f"📊 Total: {stats['attempted']}\n"
                    f"📈 Success Rate: {success_rate:.1f}%\n"
                )
                
                if success_rate >= 70:
                    result += "\n🔥 **Account flagged for review!**"
                
                context.bot.send_message(chat_id=chat_id, text=result, parse_mode="Markdown")
                
            except Exception as e:
                context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {str(e)}")
            finally:
                if chat_id in active_attacks:
                    del active_attacks[chat_id]
        
        thread = threading.Thread(target=run_attack)
        thread.daemon = True
        thread.start()

def stats_command(update, context):
    user_id = update.effective_user.id
    
    if not user_stats:
        update.message.reply_text("📊 No reports yet!")
        return
    
    message = "📊 **Your Report Stats**\n\n"
    total_success = 0
    
    for username, stats_list in user_stats.items():
        for stats in stats_list:
            total_success += stats.get('success', 0)
            message += f"@{username}: {stats.get('success', 0)}✅ ({stats.get('attempted', 0)} total)\n"
    
    message += f"\n🏆 **Total Successful Reports: {total_success}**"
    
    update.message.reply_text(message, parse_mode="Markdown")

def stop(update, context):
    chat_id = update.effective_chat.id
    
    if chat_id in active_attacks and active_attacks[chat_id].is_running:
        active_attacks[chat_id].stop()
        update.message.reply_text("🛑 Attack stopped")
        del active_attacks[chat_id]
    else:
        update.message.reply_text("❌ No running attack")

def help_command(update, context):
    update.message.reply_text(
        "📖 **Commands:**\n\n"
        "/start - Show menu\n"
        "/report @username - Start attack\n"
        "/stop - Stop attack\n"
        "/help - This guide\n\n"
        "⚠️ Only report violations!"
    )

# ==================== MAIN ====================
def main():
    print("=" * 60)
    print("🔥 INSTAGRAM MASS REPORTER")
    print("=" * 60)
    print("✅ Bot Starting...")
    
    try:
        updater = Updater(BOT_TOKEN)
        dp = updater.dispatcher
        
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("report", report))
        dp.add_handler(CommandHandler("stop", stop))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CallbackQueryHandler(button_handler))
        
        print("✅ Bot is running!")
        print("=" * 60)
        
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
