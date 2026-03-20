import qrcode
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os

# Papka yaratamiz
if not os.path.exists('static/invitations'):
    os.makedirs('static/invitations')

def generate_invitations():
    df = pd.read_csv('responses.csv')
    base_url = "http://127.0.0.1:5000/invitation/" # Saytingiz manzili

    for index, row in df.iterrows():
        guest_id = row['id']
        guest_name = row['name']
        
        # 1. QR kod yaratish
        qr_link = f"{base_url}{guest_id}"
        qr = qrcode.make(qr_link)
        qr = qr.resize((200, 200))

        # 2. Taklifnoma foni (oq rasm yaratamiz, siz o'zingizni chiroyli rasmingizni qo'ysangiz ham bo'ladi)
        img = Image.new('RGB', (600, 800), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Dizayn elementlari
        draw.rectangle([20, 20, 580, 780], outline="#d4af37", width=5)
        
        # Matnlarni yozish
        # Eslatma: Shrift yo'li kompyuteringizda turlicha bo'lishi mumkin
        try:
            font_title = ImageFont.truetype("arial.ttf", 40)
            font_name = ImageFont.truetype("arial.ttf", 30)
        except:
            font_title = ImageFont.load_default()
            font_name = ImageFont.load_default()

        draw.text((300, 100), "TAKLIFNOMA", fill="#d4af37", font=font_title, anchor="mm")
        draw.text((300, 200), guest_name, fill="black", font=font_name, anchor="mm")
        draw.text((300, 250), "Sizni to'yimizda kutamiz!", fill="gray", font=font_name, anchor="mm")

        # 3. QR kodni rasmga yopishtirish
        img.paste(qr, (200, 400))
        
        draw.text((300, 650), "Batafsil ma'lumot uchun", fill="black", font=font_name, anchor="mm")
        draw.text((300, 680), "QR kodni skaner qiling", fill="black", font=font_name, anchor="mm")

        # Saqlash
        img.save(f'static/invitations/taklifnoma_{guest_id}.png')
        print(f"{guest_name} uchun taklifnoma tayyor!")

if __name__ == "__main__":
    generate_invitations()