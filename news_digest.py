import markdown
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

# --- PERFIL DEL LECTOR ---
# Todo lo que sigue está ajustado para un Gerente de TI: las búsquedas
# priorizan seguridad, infraestructura, presupuesto y decisiones de negocio,
# y el prompt de IA le pide a la IA que redacte pensando en ese lector.
PERFIL_LECTOR = "un Gerente de TI (CIO) de una empresa mediana en Chile"

def get_news(query, language="es"):
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

def summarize_with_ai(news_text, topic, enfoque_gerencial):
    client = Groq(api_key=GROQ_API_KEY)
    prompt = f"""Eres un editor de noticias que redacta un boletín ejecutivo para {PERFIL_LECTOR}.
Tengo estas noticias de {topic} del día de hoy:

{news_text}

Redacta un resumen ejecutivo en español, bien estructurado, con las 5 noticias
más importantes para este lector. Usa bullet points con emojis y un tono
profesional pero directo. Máximo 400 palabras.

Criterios de selección y enfoque:
{enfoque_gerencial}

Descarta noticias de puro interés de consumidor final (lanzamientos de
gadgets, rumores de productos, etc.) que no tengan relevancia para la
gestión de una empresa. Cuando una noticia implique un riesgo, una decisión
o una oportunidad para el área de TI, indícalo en una frase corta al final
del bullet (por ejemplo: "→ Riesgo: evaluar parches en servidores propios")."""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600
    )
    return response.choices[0].message.content

def send_email(tech_summary, eco_summary):
    today = date.today().strftime("%d/%m/%Y")

    html = f"""
    <html><body style="font-family: Georgia, serif; max-width: 680px; margin: auto; background: #f9f9f9; padding: 20px;">
        <div style="background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h1 style="color: #1a1a2e; border-bottom: 3px solid #e74c3c; padding-bottom: 10px;">
                📰 Digest Diario — {today}
            </h1>

            <h2 style="color: #2980b9; margin-top: 30px;">💻 Tecnología</h2>
            <div style="line-height: 1.8; color: #333;">
                {markdown.markdown(tech_summary)}
            </div>

            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">

            <h2 style="color: #27ae60;">📈 Economía</h2>
            <div style="line-height: 1.8; color: #333;">
                {markdown.markdown(eco_summary)}
            </div>

            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #aaa; font-size: 12px; text-align: center;">
                Generado automáticamente con IA • {today}
            </p>
        </div>
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
    # Búsqueda de "Tecnología" centrada en lo que le importa a un Gerente de
    # TI: seguridad, continuidad operativa, cloud e infraestructura, y
    # adopción de IA en empresas (no gadgets de consumo).
    print("📡 Obteniendo noticias de tecnología...")
    tech_query = (
        '(ciberseguridad OR ransomware OR "cloud computing" '
        'OR "transformación digital" OR "infraestructura TI")'
    )
    tech_news = get_news(tech_query)
    tech_enfoque = (
        "- Prioriza: incidentes de seguridad y vulnerabilidades relevantes para empresas, "
        "cambios en proveedores cloud/infraestructura, adopción de IA en compañías, "
        "y normativas o cumplimiento (ej. protección de datos).\n"
        "- Para cada noticia relevante, señala brevemente el posible impacto en "
        "operación, riesgo o presupuesto de un área de TI."
    )

    # Búsqueda de "Economía" centrada en variables que afectan el presupuesto
    # y las decisiones de TI (dólar para licencias/hardware, inflación, tasas,
    # gasto en tecnología), no economía general de consumo.
    print("📡 Obteniendo noticias de economía...")
    eco_query = (
        '("economía chilena" OR dólar OR inflación '
        'OR "presupuesto TI" OR "gasto en tecnología")'
    )
    eco_news = get_news(eco_query)
    eco_enfoque = (
        "- Prioriza: tipo de cambio y su efecto en compras de software/hardware en dólares, "
        "inflación y tasas de interés (impacto en presupuesto e inversión en TI), "
        "y tendencias de gasto o inversión en tecnología en empresas.\n"
        "- Para cada noticia relevante, indica brevemente qué implicancia tiene "
        "para planificar el presupuesto o las inversiones del área de TI."
    )

    print("🤖 Resumiendo con IA...")
    tech_summary = summarize_with_ai(tech_news, "tecnología", tech_enfoque)
    eco_summary  = summarize_with_ai(eco_news, "economía", eco_enfoque)

    print("📧 Enviando correo...")
    send_email(tech_summary, eco_summary)
