"""
Tienda de Ropa — WhatsApp Bot
WhatsApp (Meta) + Gemini 2.5 Flash (Google AI)
Deploy en Vercel — Sin Shopify, catálogo local
"""

import json
import os
import re
import base64
import datetime
import httpx
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ──────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────
VERIFY_TOKEN   = os.environ.get("VERIFY_TOKEN", "whatsapp_verify_2026")
META_TOKEN     = os.environ.get("META_TOKEN", "")        # El valor real va en Vercel > Settings > Env Variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")   # El valor real va en Vercel > Settings > Env Variables

GEMINI_MODEL = "gemini-2.5-flash-preview-05-20"
GEMINI_URL   = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# ──────────────────────────────────────────
# CATÁLOGO LOCAL DE PRODUCTOS
# ──────────────────────────────────────────
CATALOGO = [
    {
        "id": 1,
        "titulo": "Camiseta Básica",
        "descripcion": "Camiseta de algodón 100%, corte recto, cuello redondo.",
        "variantes": [
            {"talla": "XS", "color": "Blanco",  "precio": "25000", "stock": 10},
            {"talla": "S",  "color": "Blanco",  "precio": "25000", "stock": 8},
            {"talla": "M",  "color": "Blanco",  "precio": "25000", "stock": 6},
            {"talla": "L",  "color": "Blanco",  "precio": "25000", "stock": 4},
            {"talla": "S",  "color": "Negro",   "precio": "25000", "stock": 7},
            {"talla": "M",  "color": "Negro",   "precio": "25000", "stock": 5},
            {"talla": "L",  "color": "Negro",   "precio": "25000", "stock": 3},
            {"talla": "M",  "color": "Gris",    "precio": "25000", "stock": 5},
        ]
    },
    {
        "id": 2,
        "titulo": "Jean Slim Fit",
        "descripcion": "Jean de mezclilla stretch, corte slim, cinco bolsillos.",
        "variantes": [
            {"talla": "28", "color": "Azul Oscuro", "precio": "89000", "stock": 5},
            {"talla": "30", "color": "Azul Oscuro", "precio": "89000", "stock": 7},
            {"talla": "32", "color": "Azul Oscuro", "precio": "89000", "stock": 6},
            {"talla": "34", "color": "Azul Oscuro", "precio": "89000", "stock": 4},
            {"talla": "30", "color": "Negro",       "precio": "89000", "stock": 5},
            {"talla": "32", "color": "Negro",       "precio": "89000", "stock": 4},
        ]
    },
    {
        "id": 3,
        "titulo": "Sudadera con Capucha",
        "descripcion": "Hoodie de felpa francesa, bolsillo canguro, unisex.",
        "variantes": [
            {"talla": "S",  "color": "Gris Melange", "precio": "75000", "stock": 8},
            {"talla": "M",  "color": "Gris Melange", "precio": "75000", "stock": 10},
            {"talla": "L",  "color": "Gris Melange", "precio": "75000", "stock": 6},
            {"talla": "XL", "color": "Gris Melange", "precio": "75000", "stock": 3},
            {"talla": "M",  "color": "Negro",        "precio": "75000", "stock": 7},
            {"talla": "L",  "color": "Negro",        "precio": "75000", "stock": 5},
        ]
    },
    {
        "id": 4,
        "titulo": "Vestido Floral",
        "descripcion": "Vestido midi con estampado floral, manga corta, tela liviana.",
        "variantes": [
            {"talla": "XS", "color": "Rosa",  "precio": "65000", "stock": 4},
            {"talla": "S",  "color": "Rosa",  "precio": "65000", "stock": 6},
            {"talla": "M",  "color": "Rosa",  "precio": "65000", "stock": 5},
            {"talla": "S",  "color": "Azul",  "precio": "65000", "stock": 4},
            {"talla": "M",  "color": "Azul",  "precio": "65000", "stock": 3},
        ]
    },
    {
        "id": 5,
        "titulo": "Chaqueta de Cuero",
        "descripcion": "Chaqueta de cuero sintético, cierre frontal, bolsillos laterales.",
        "variantes": [
            {"talla": "S", "color": "Negro", "precio": "180000", "stock": 3},
            {"talla": "M", "color": "Negro", "precio": "180000", "stock": 4},
            {"talla": "L", "color": "Negro", "precio": "180000", "stock": 2},
            {"talla": "M", "color": "Café",  "precio": "180000", "stock": 3},
        ]
    },
    {
        "id": 6,
        "titulo": "Falda Midi",
        "descripcion": "Falda de tela plisada, elástico en cintura, largo hasta la rodilla.",
        "variantes": [
            {"talla": "XS", "color": "Beige", "precio": "55000", "stock": 5},
            {"talla": "S",  "color": "Beige", "precio": "55000", "stock": 7},
            {"talla": "M",  "color": "Beige", "precio": "55000", "stock": 6},
            {"talla": "S",  "color": "Negro", "precio": "55000", "stock": 5},
            {"talla": "M",  "color": "Negro", "precio": "55000", "stock": 4},
        ]
    },
    {
        "id": 7,
        "titulo": "Polo Deportivo",
        "descripcion": "Polo de tela piqué, cuello con botones, ideal para deporte o casual.",
        "variantes": [
            {"talla": "S",  "color": "Blanco",      "precio": "45000", "stock": 8},
            {"talla": "M",  "color": "Blanco",      "precio": "45000", "stock": 10},
            {"talla": "L",  "color": "Blanco",      "precio": "45000", "stock": 7},
            {"talla": "XL", "color": "Blanco",      "precio": "45000", "stock": 5},
            {"talla": "M",  "color": "Azul Marino", "precio": "45000", "stock": 6},
            {"talla": "L",  "color": "Azul Marino", "precio": "45000", "stock": 4},
        ]
    },
    {
        "id": 8,
        "titulo": "Blusa de Lino",
        "descripcion": "Blusa suelta de lino natural, manga larga enrollable, cuello en V.",
        "variantes": [
            {"talla": "XS", "color": "Blanco",      "precio": "48000", "stock": 6},
            {"talla": "S",  "color": "Blanco",      "precio": "48000", "stock": 8},
            {"talla": "M",  "color": "Blanco",      "precio": "48000", "stock": 5},
            {"talla": "S",  "color": "Verde Oliva", "precio": "48000", "stock": 4},
            {"talla": "M",  "color": "Verde Oliva", "precio": "48000", "stock": 6},
        ]
    },
]

CATALOGO_STR = json.dumps(CATALOGO, ensure_ascii=False, indent=2)

# ──────────────────────────────────────────
# MEMORIA EN PROCESO (Vercel = efímero)
# Para persistencia real usa Vercel KV o Redis
# ──────────────────────────────────────────
conversations: dict = {}   # phone -> list of {role, content}
orders: list = []          # Órdenes simuladas (sin Shopify)


# ──────────────────────────────────────────
# META — descargar imagen
# ──────────────────────────────────────────
def download_image(media_id: str) -> tuple:
    """Descarga una imagen de WhatsApp y retorna (bytes, mime_type)."""
    headers = {"Authorization": f"Bearer {META_TOKEN}"}
    try:
        r = httpx.get(
            f"https://graph.facebook.com/v19.0/{media_id}",
            headers=headers, timeout=10
        )
        data = r.json()
        media_url = data.get("url", "")
        mime_type = data.get("mime_type", "image/jpeg")
        r2 = httpx.get(media_url, headers=headers, timeout=15)
        return r2.content, mime_type
    except Exception as e:
        print(f"Error descargando imagen: {e}")
        return None, None


# ──────────────────────────────────────────
# META — enviar mensaje de texto
# ──────────────────────────────────────────
def send_whatsapp_message(phone_number_id: str, to: str, text: str):
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {META_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text}
    }
    httpx.post(url, headers=headers, json=payload, timeout=10)


# ──────────────────────────────────────────
# GEMINI 2.5 FLASH — llamar a la API
# ──────────────────────────────────────────
def call_gemini(
    history: list,
    user_name: str,
    phone: str,
    image_bytes: bytes = None,
    mime_type: str = None,
    caption: str = ""
) -> str:
    system_prompt = f"""Eres un asistente de ventas de una tienda de ropa por WhatsApp. Tu nombre es Moda Assistant.

Tu trabajo es ayudar a los clientes a encontrar prendas, informar sobre tallas, colores, precios y disponibilidad, y guiarlos para concretar una compra.

CATÁLOGO ACTUAL DE PRODUCTOS:
{CATALOGO_STR}

REGLAS:
1. Responde siempre en español, de forma amable y natural (sin markdown, sin asteriscos).
2. Si el cliente pregunta por un producto, busca en el catálogo y da la info de tallas, colores y precio.
3. Si el cliente manda una imagen, analiza qué prenda es y busca la más similar en el catálogo.
4. Si una talla o color no está disponible, díselo y ofrece alternativas del catálogo.
5. Si el cliente quiere comprar, pídele en orden: nombre completo, dirección de envío, confirma producto/talla/color.
6. Cuando tengas TODOS los datos, incluye al final de tu mensaje exactamente esto (sin espacios extra):
DATO_VENTA_JSON:{{"accion":"crear_orden","cliente":{{"nombre":"NOMBRE","telefono":"TELEFONO","direccion":"DIRECCION"}},"producto":{{"titulo":"TITULO","talla":"TALLA","color":"COLOR","precio":"PRECIO","cantidad":1}}}}
7. Sé breve y conversacional. Máximo 3-4 líneas por respuesta.
8. Si preguntan algo fuera de la tienda, redirige amablemente.

Nombre del cliente: {user_name}
Teléfono: {phone}"""

    # Construir el array de contents para Gemini
    contents = []
    for msg in history:
        role = msg["role"]  # "user" o "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })

    # Si el mensaje actual tiene imagen, reemplazar las parts del último mensaje
    if image_bytes and contents and contents[-1]["role"] == "user":
        contents[-1]["parts"] = [
            {
                "inline_data": {
                    "mime_type": mime_type or "image/jpeg",
                    "data": base64.b64encode(image_bytes).decode("utf-8")
                }
            },
            {
                "text": caption if caption else "El cliente envió esta imagen. ¿Tienes algo parecido en el catálogo?"
            }
        ]

    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": 1024,
            "temperature": 0.7
        }
    }

    # Validar que la API key esté configurada
    if not GEMINI_API_KEY:
        print("[ERROR] GEMINI_API_KEY no está configurada en las variables de entorno de Vercel.")
        return "Lo siento, el servicio no está configurado correctamente."

    r = None
    try:
        r = httpx.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=payload,
            timeout=30
        )
        result = r.json()

        # Detectar error explícito de la API de Gemini
        if "error" in result:
            err = result["error"]
            print(f"[GEMINI ERROR] code={err.get('code')} status={err.get('status')} message={err.get('message')}")
            return "Lo siento, tuve un problema técnico. Intenta de nuevo en un momento."

        return result["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        raw = r.text if r is not None else "(sin respuesta)"
        print(f"[GEMINI EXCEPTION] {e} — Respuesta raw: {raw}")
        return "Lo siento, tuve un problema técnico. Intenta de nuevo en un momento."


# ──────────────────────────────────────────
# REGISTRAR ORDEN (simulado, sin Shopify)
# ──────────────────────────────────────────
def register_order(venta_data: dict) -> str:
    order_num = f"WA-{len(orders) + 1:04d}"
    orders.append({
        "numero": order_num,
        "fecha": datetime.datetime.now().isoformat(),
        **venta_data
    })
    print(f"[ORDEN] {order_num}: {json.dumps(venta_data, ensure_ascii=False)}")
    return order_num


# ──────────────────────────────────────────
# PROCESAR MENSAJE ENTRANTE
# ──────────────────────────────────────────
def process_message(body: dict):
    try:
        entry = body["entry"][0]
        change = entry["changes"][0]["value"]
        messages = change.get("messages", [])

        if not messages:
            return  # Status update, no es un mensaje real

        msg = messages[0]
        phone = msg["from"]
        phone_number_id = change["metadata"]["phone_number_id"]
        user_name = change.get("contacts", [{}])[0].get("profile", {}).get("name", "Cliente")
        msg_type = msg["type"]

        history = conversations.get(phone, [])

        image_bytes = None
        mime_type_img = None
        caption = ""

        # ── Mensaje de TEXTO ──
        if msg_type == "text":
            user_text = msg["text"]["body"]
            history.append({"role": "user", "content": user_text})

        # ── Mensaje de IMAGEN ──
        elif msg_type == "image":
            media_id = msg["image"]["id"]
            caption = msg["image"].get("caption", "")
            image_bytes, mime_type_img = download_image(media_id)
            # En el historial guardamos descripción textual (no los bytes)
            history.append({
                "role": "user",
                "content": caption if caption else "El cliente envió una imagen de una prenda."
            })

        else:
            # Audio, video, sticker — ignorar
            return

        # ── Llamar a Gemini 2.5 Flash ──
        gemini_response = call_gemini(
            history, user_name, phone,
            image_bytes=image_bytes,
            mime_type=mime_type_img,
            caption=caption
        )

        # ── Detectar si hay datos de venta ──
        venta_match = re.search(r'DATO_VENTA_JSON:(\{.+?\})(?:\n|$)', gemini_response)
        venta_data = None
        mensaje_limpio = gemini_response

        if venta_match:
            try:
                venta_data = json.loads(venta_match.group(1))
                mensaje_limpio = re.sub(r'DATO_VENTA_JSON:\{.+?\}(?:\n|$)', '', gemini_response).strip()
            except Exception:
                pass

        # ── Guardar respuesta en historial (rol "model" para Gemini) ──
        history.append({"role": "model", "content": mensaje_limpio})
        conversations[phone] = history[-20:]  # Últimos 20 mensajes

        # ── Si hay venta, registrar orden ──
        if venta_data:
            order_num = register_order(venta_data)
            mensaje_limpio += f"\n\n✅ Pedido {order_num} registrado. Te contactaremos pronto para coordinar el pago y envío. ¡Gracias!"

        # ── Enviar respuesta por WhatsApp ──
        send_whatsapp_message(phone_number_id, phone, mensaje_limpio)

    except Exception as e:
        print(f"Error procesando mensaje: {e}")


# ──────────────────────────────────────────
# HANDLER DE VERCEL
# ──────────────────────────────────────────
class handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # Silenciar logs por defecto

    # ── GET — verificación del webhook de Meta ──
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        mode      = params.get("hub.mode", [None])[0]
        token     = params.get("hub.verify_token", [None])[0]
        challenge = params.get("hub.challenge", [None])[0]

        if mode == "subscribe" and token == VERIFY_TOKEN:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(challenge.encode())
        else:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Forbidden")

    # ── POST — mensajes entrantes de WhatsApp ──
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(content_length)

        # Responder 200 de inmediato a Meta (evita reenvíos)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

        try:
            body = json.loads(body_raw)
            process_message(body)
        except Exception as e:
            print(f"Error parseando body: {e}")