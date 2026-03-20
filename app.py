import os
import json
import qrcode
import zipfile
import io
import shutil
import pandas as pd
from flask import Flask, render_template, request, redirect, session, url_for, send_file
from PIL import Image, ImageDraw, ImageFont, ImageOps

app = Flask(__name__)
app.secret_key = "wedding_2026_ultra_final_v3"

# --- YO'LLAR ---
BASE_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(BASE_DIR_PATH, 'weddings')
STATIC_DIR = os.path.join(BASE_DIR_PATH, 'static')
INVITES_DIR = os.path.join(STATIC_DIR, 'invitations')
FONT_DIR = os.path.join(STATIC_DIR, 'fonts')
TEMPLATES_CONFIG_DIR = os.path.join(BASE_DIR_PATH, 'saved_templates')

# Papkalarni avtomatik yaratish
for path in [BASE_DIR, INVITES_DIR, FONT_DIR, TEMPLATES_CONFIG_DIR]:
    if not os.path.exists(path): os.makedirs(path)

FONT_CURSIVE = os.path.join(FONT_DIR, 'GreatVibes-Regular.ttf')
FONT_SERIF = os.path.join(FONT_DIR, 'PlayfairDisplay-VariableFont_wght.ttf')

# --- YORDAMCHI FUNKSIYALAR ---
def get_font(path, size):
    try:
        return ImageFont.truetype(path, int(size)) if os.path.exists(path) else ImageFont.load_default()
    except:
        return ImageFont.load_default()

def format_uzb_date(date_str):
    months = {"01":"yanvar","02":"fevral","03":"mart","04":"aprel","05":"may","06":"iyun","07":"iyul","08":"avgust","09":"sentyabr","10":"oktyabr","11":"noyabr","12":"dekabr"}
    try:
        dt = date_str.split("T")[0] if "T" in date_str else date_str.split(" ")[0]
        y, m, d = dt.split("-")
        return f"{int(d)}-{months[m]}, {y}-yil"
    except:
        return date_str

def create_pro_invitation(wedding_name, guest_id, name, table='', seat=''):
    w_path = os.path.join(BASE_DIR, wedding_name)
    with open(os.path.join(w_path, 'info.json'), 'r', encoding='utf-8') as f:
        w_info = json.load(f)

    # 1. Canvas yaratish
    img = Image.new('RGB', (800, 1200), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    gold = "#C5A059"
    dark = "#222222"

    # 2. Tashqi ramka
    draw.rectangle([20, 20, 780, 1180], outline=gold, width=2)

    # 3. RASM CHIZISH QISMI (MUHIM!)
    wedding_photo_name = w_info.get('photo', '')
    photo_path = os.path.join(INVITES_DIR, wedding_photo_name)
    
    # Rasm ramkasi koordinatalari
    frame_coords = [250, 70, 550, 370]
    draw.rectangle(frame_coords, outline=gold, width=2)

    if os.path.exists(photo_path) and os.path.isfile(photo_path):
        try:
            raw_photo = Image.open(photo_path).convert("RGB")
            # Rasmni ramkaga moslab qirqish va joylash
            photo_resized = ImageOps.fit(raw_photo, (298, 298), centering=(0.5, 0.5))
            img.paste(photo_resized, (251, 71))
        except Exception as e:
            print(f"Rasm yuklashda xato: {e}")
            draw.text((400, 220), "❤️", fill=gold, font=get_font(FONT_SERIF, 80), anchor="mm")
    else:
        # Agar rasm topilmasa yurakcha chizadi
        draw.text((400, 220), "❤️", fill=gold, font=get_font(FONT_SERIF, 80), anchor="mm")

    # 4. Kuyov & Kelin ismlari
    draw.text((400, 450), f"{w_info.get('groom')} & {w_info.get('bride')}", 
              fill=gold, font=get_font(FONT_CURSIVE, 80), anchor="mm")

    # 5. Mehmon ismi
    draw.text((400, 530), "HURMATLI", fill="#888888", font=get_font(FONT_SERIF, 22), anchor="mm")
    draw.text((400, 590), name.upper(), fill=dark, font=get_font(FONT_SERIF, 55), anchor="mm")
    draw.line([300, 630, 500, 630], fill=gold, width=2)

    # 6. Asosiy taklif matni
    invite_msg = ("Siz(lar)ni farzandlarimizning nikoh to‘yi munosabati bilan\n"
                  "tashkil etilgan tantanali dasturxonimizning\n"
                  "qadrli mehmoni bo‘lishga taklif qilamiz!")
    
    draw.multiline_text((400, 720), invite_msg, fill=dark, 
                        font=get_font(FONT_SERIF, 24), 
                        anchor="mm", align="center", spacing=12)

    # 7. STOL VA JOY (Taklifdan keyin)
    place_info = ""
    if table and str(table).strip() != "":
        place_info += f"{table}-stol"
    if seat and str(seat).strip() != "":
        if place_info: place_info += ", "
        place_info += f"{seat}-joy"
    
    if place_info:
        draw.text((400, 810), place_info, fill=gold, font=get_font(FONT_SERIF, 35), anchor="mm")

    # 8. Sana va Manzil
    draw.text((400, 880), "Kuni va vaqti:", fill="#888888", font=get_font(FONT_SERIF, 20), anchor="mm")
    draw.text((400, 920), format_uzb_date(w_info.get('date')), fill=dark, font=get_font(FONT_SERIF, 32), anchor="mm")
    
    draw.text((400, 990), "Manzil:", fill="#888888", font=get_font(FONT_SERIF, 20), anchor="mm")
    draw.text((400, 1030), w_info.get('venue'), fill=dark, font=get_font(FONT_SERIF, 32), anchor="mm")

    # 9. Oila nomi
    family = w_info.get('family_name', 'Fayziyevlar oilasi')
    draw.text((400, 1110), f"Hurmat bilan: {family}", fill=gold, font=get_font(FONT_SERIF, 28), anchor="mm")

    # 10. QR Kod
    qr_url = f"http://{request.host}/invitation/{wedding_name}/{guest_id}"
    qr_img = qrcode.make(qr_url).convert('RGB').resize((90, 90))
    img.paste(qr_img, (680, 1080)) 

    # Saqlash
    save_path = os.path.join(INVITES_DIR, wedding_name)
    if not os.path.exists(save_path): os.makedirs(save_path)
    img.save(os.path.join(save_path, f'guest_{guest_id}.jpg'), "JPEG", quality=95)

# --- ROUTES ---

@app.route('/admin/delete_guests/<wedding_name>', methods=['POST'])
def delete_guests(wedding_name):
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    guest_ids = request.form.getlist('guest_ids')
    csv_path = os.path.join(BASE_DIR, wedding_name, 'guests.csv')
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df = df[~df['id'].astype(str).isin(guest_ids)]
        df.to_csv(csv_path, index=False)
        for g_id in guest_ids:
            img_path = os.path.join(INVITES_DIR, wedding_name, f'guest_{g_id}.jpg')
            if os.path.exists(img_path): os.remove(img_path)
    return redirect(url_for('view_wedding', name=wedding_name))

@app.route('/')
@app.route('/admin')
def admin_root():
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('password') == "admin123":
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
    return render_template('login.html')

@app.route('/admin/panel')
def admin_panel():
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    weddings = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]
    saved_ts = [f.replace('.json', '') for f in os.listdir(TEMPLATES_CONFIG_DIR) if f.endswith('.json')]
    return render_template('admin_main.html', weddings=weddings, saved_templates=saved_ts)

@app.route('/admin/add_wedding', methods=['POST'])
def add_wedding():
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    title = request.form.get('wedding_name').strip().replace(" ", "_")
    w_path = os.path.join(BASE_DIR, title)
    if not os.path.exists(w_path):
        os.makedirs(w_path)
        photo = request.files.get('photo')
        photo_name = f"photo_{title}.jpg" if photo else "default_wedding.jpg"
        if photo: photo.save(os.path.join(INVITES_DIR, photo_name))
        
        info = {
            "groom": request.form.get('groom'),
            "bride": request.form.get('bride'),
            "venue": request.form.get('venue'),
            "date": request.form.get('date'),
            "photo": photo_name,
            "family_name": request.form.get('family_name', ''),
            "location": request.form.get('location', '#'),
            "template_choice": request.form.get('template_choice', 'default')
        }
        with open(os.path.join(w_path, 'info.json'), 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=4)
        
        # CSV ustunlari to'g'irlandi: table va seat qo'shildi
        pd.DataFrame(columns=['id', 'name', 'table', 'seat']).to_csv(os.path.join(w_path, 'guests.csv'), index=False)
    return render_template('choose_mode.html', wedding_name=title)

@app.route('/admin/wedding/<name>')
def view_wedding(name):
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    df = pd.read_csv(os.path.join(BASE_DIR, name, 'guests.csv'))
    return render_template('wedding_details.html', wedding_name=name, guests=df.to_dict(orient='records'))

@app.route('/admin/add_guest/<wedding_name>', methods=['POST'])
def add_guest(wedding_name):
    csv_path = os.path.join(BASE_DIR, wedding_name, 'guests.csv')
    df = pd.read_csv(csv_path)
    
    # Yangi ID aniqlash
    new_id = int(df['id'].max() + 1) if not df.empty else 1
    
    guest_name = request.form.get('name')
    table_no = request.form.get('table', '') # Formadan stol raqami
    seat_no = request.form.get('seat', '')   # Formadan joy raqami
    
    # Ma'lumotlarni qo'shish
    new_guest = pd.DataFrame([[new_id, guest_name, table_no, seat_no]], columns=['id', 'name', 'table', 'seat'])
    df = pd.concat([df, new_guest], ignore_index=True)
    df.to_csv(csv_path, index=False)
    
    # Rasmni barcha parametrlar bilan yaratish
    create_pro_invitation(wedding_name, new_id, guest_name, table_no, seat_no)
    
    return redirect(url_for('view_wedding', name=wedding_name))

@app.route('/admin/delete_weddings', methods=['POST'])
def delete_weddings():
    for w in request.form.getlist('wedding_ids'):
        shutil.rmtree(os.path.join(BASE_DIR, w), ignore_errors=True)
        shutil.rmtree(os.path.join(INVITES_DIR, w), ignore_errors=True)
    return redirect(url_for('admin_panel'))

@app.route('/admin/download_all/<wedding_name>')
def download_all(wedding_name):
    path = os.path.join(INVITES_DIR, wedding_name)
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for root, dirs, files in os.walk(path):
            for file in files:
                zf.write(os.path.join(root, file), file)
    memory_file.seek(0)
    return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name=f'{wedding_name}.zip')

@app.route('/invitation/<wedding_name>/<int:guest_id>')
def invitation(wedding_name, guest_id):
    w_path = os.path.join(BASE_DIR, wedding_name)
    with open(os.path.join(w_path, 'info.json'), 'r', encoding='utf-8') as f:
        w_info = json.load(f)
    df = pd.read_csv(os.path.join(w_path, 'guests.csv'))
    guest = df[df['id'] == guest_id].iloc[0].to_dict()
    return render_template('index.html', guest=guest, w_info=w_info)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin/editor/<wedding_name>')
def editor(wedding_name):
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    w_path = os.path.join(BASE_DIR, wedding_name)
    with open(os.path.join(w_path, 'info.json'), 'r', encoding='utf-8') as f:
        w_info = json.load(f)
    return render_template('editor.html', wedding_name=wedding_name, w_info=w_info)

@app.route('/admin/save_template', methods=['POST'])
def save_template():
    if not session.get('logged_in'): return {"status": "error"}, 403
    data = request.json
    template_name = data.get('template_name', 'unnamed_template')
    file_path = os.path.join(TEMPLATES_CONFIG_DIR, f"{template_name}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data['config'], f, ensure_ascii=False, indent=4)
    return {"status": "success", "message": "Shablon saqlandi!"}

@app.context_processor
def utility_processor():
    return dict(format_uzb_date=format_uzb_date)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)