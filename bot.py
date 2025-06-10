
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls, GroupCall
from pytgcalls.types import AudioPiped
from yt_dlp import YoutubeDL

# API məlumatları (şəkildən götürülüb)
API_ID = 23342849
API_HASH = "59f3a8a7a5cfb06d20c3d983d4163e55"

# Bot tokenini əldə etmək üçün @BotFather ilə danışmalısınız
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Qrup ID-si
CHAT_ID = -1001740886678

app = Client("ZengMahniBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call_py = PyTgCalls(app)

# Qrup zəngini idarə etmək üçün lüğət
group_calls = {}

# Mahnı növbəsi lüğəti
music_queue = {}

# yt-dlp konfiqurasiyası
ytdl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0', # IPv4 only
}

async def play_next_song(chat_id: int):
    if chat_id in music_queue and music_queue[chat_id]:
        next_song = music_queue[chat_id].pop(0)
        try:
            await group_calls[chat_id].play(AudioPiped(next_song['file_path']))
            await app.send_message(chat_id, f"İndi oxunur: **{next_song['title']}**")
        except Exception as e:
            await app.send_message(chat_id, f"Növbəti mahnını oxutarkən xəta baş verdi: {e}")
            await play_next_song(chat_id) # Növbəti mahnıya keç
    else:
        if chat_id in group_calls:
            await group_calls[chat_id].stop()
            del group_calls[chat_id]
        await app.send_message(chat_id, "Növbədə mahnı qalmadı. Zəngdən çıxıldı.")

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    await message.reply_text(
        "Salam! Mən Telegram zəngində mahnı oxuyan botam.\n\n"
        "Əmrlər:\n"
        "/oxu [mahnı linki və ya adı] - Mahnını zəngdə oxutmağa başlayır.\n"
        "/dayan - Mahnını dayandırır və zəngdən çıxır.\n"
        "/keç - Növbəti mahnıya keçir (əgər növbə varsa).\n"
        "/komutlar - Bu mesajı yenidən göstərir."
    )

@app.on_message(filters.command("komutlar") & filters.private)
async def commands_command(client: Client, message: Message):
    await start_command(client, message) # Eyni mesajı göstəririk

@app.on_message(filters.command("oxu") & filters.group)
async def play_music(client: Client, message: Message):
    if message.chat.id != CHAT_ID:
        return

    query = " ".join(message.command[1:])
    if not query:
        await message.reply_text("Zəhmət olmasa, mahnı linki və ya adını daxil edin. Məsələn: /oxu https://youtube.com/watch?v=dQw4w9WgXcQ")
        return

    await message.reply_text(f"Mahnı axtarılır: **{query}**...")

    try:
        with YoutubeDL(ytdl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0] # Playlistin ilk mahnısını götürürük
            
            file_path = ydl.prepare_filename(info)
            ydl.download([query]) # Mahnını yüklə

        song_info = {
            'title': info.get('title', 'Naməlum mahnı'),
            'file_path': file_path
        }

        if message.chat.id not in group_calls:
            group_call = GroupCall(client, CHAT_ID)
            group_calls[message.chat.id] = group_call
            await group_call.start()
            music_queue[message.chat.id] = []
            music_queue[message.chat.id].append(song_info)
            await play_next_song(message.chat.id)
        else:
            music_queue[message.chat.id].append(song_info)
            await message.reply_text(f"**{song_info['title']}** növbəyə əlavə edildi. Növbədə {len(music_queue[message.chat.id])} mahnı var.")

    except Exception as e:
        await message.reply_text(f"Mahnı yüklənərkən və ya oxunarkən xəta baş verdi: {e}")

@app.on_message(filters.command("dayan") & filters.group)
async def stop_music(client: Client, message: Message):
    if message.chat.id != CHAT_ID:
        return

    if message.chat.id in group_calls:
        await group_calls[message.chat.id].stop()
        del group_calls[message.chat.id]
        music_queue[message.chat.id] = [] # Növbəni təmizlə
        await message.reply_text("Mahnı dayandırıldı və zəngdən çıxıldı.")
    else:
        await message.reply_text("Hazırda heç bir mahnı oxunmur.")

@app.on_message(filters.command("keç") & filters.group)
async def skip_music(client: Client, message: Message):
    if message.chat.id != CHAT_ID:
        return

    if message.chat.id in group_calls:
        if music_queue[message.chat.id]:
            await message.reply_text("Növbəti mahnıya keçilir...")
            await group_calls[message.chat.id].stop() # Cari mahnını dayandır
            await play_next_song(message.chat.id) # Növbəti mahnını oxut
        else:
            await message.reply_text("Növbədə mahnı yoxdur.")
    else:
        await message.reply_text("Hazırda heç bir mahnı oxunmur.")

print("Bot işə düşür...")
app.run()


