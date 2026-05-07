import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from groq import Groq
from datetime import date

# --- CONFIGURACIÓN (via variables de entorno en GitHub) ---
NEWS_API_KEY = os.environ["NEWS_API_KEY"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GMAIL_USER   = os.environ["GMAIL_USER"]
GMAIL_PASS   = os.environ["GMAIL_PASS"]   # App Password de Google
EMAIL_TO     = os.environ["EMAIL_TO"]

def get_news(category, query, language="es"):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": language,
        "sortBy": "publishedAt",
        "pageSize": 10,
        "apiKey": NEWS_API_KEY
    }
    r = requests.get(url, params=params)
    articles = r.json().get("articles", [])
    # Retorna titulares + descripción
    return "\n".join([
        f"- {a['title']}: {a.get('description','')}"
        for a in articles if a.get('title')
    ])

def summarize_with_ai(news_text, topic):
    client = Groq(api_key=GROQ_API_KEY)
    prompt = f"""Eres un editor de noticias profesional. 
Tengo estas noticias de {topic} del día de hoy:

{news_text}

Redacta un resumen ejecutivo en español, bien estructurado, 
con las 5 noticias más importantes. Usa bullet points con emojis 
y un tono profesional pero amigable. Máximo 400 palabras."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600
    )
    return response.choices[0].message.content

def send_email(tech_summary, eco_summary):
    today = date.today().strftime("%d/%m/%Y")
    
    html = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 650px; margin: auto;">
        <h1 style="color: #1a1a2e;">📰 Digest Diario — {today}</h1>
        
        <h2 style="color: #16213e;">💻 Tecnología</h2>
        <p style="white-space: pre-line;">{tech_summary}</p>
        
        <hr>
        
        <h2 style="color: #0f3460;">📈 Economía</h2>
        <p style="white-space: pre-line;">{eco_summary}</p>
        
        <hr>
        <p style="color: #888; font-size: 12px;">
            Generado automáticamente con IA • {today}
        </p>
    </body></html>
    """
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📰 Noticias del día — {today}"
    msg["From"]    = GMAIL_USER
    msg["To"]      = EMAIL_TO
    msg.attach(MIMEText(html, "html"))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, EMAIL_TO, msg.as_string())
    print("✅ Correo enviado correctamente")

if __name__ == "__main__":
    print("📡 Obteniendo noticias de tecnología...")
    tech_news = get_news("tecnología", "tecnología inteligencia artificial")
    
    print("📡 Obteniendo noticias de economía...")
    eco_news = get_news("economía", "economía finanzas mercados Chile")
    
    print("🤖 Resumiendo con IA...")
    tech_summary = summarize_with_ai(tech_news, "tecnología")
    eco_summary  = summarize_with_ai(eco_news, "economía")
    
    print("📧 Enviando correo...")
    send_email(tech_summary, eco_summary)