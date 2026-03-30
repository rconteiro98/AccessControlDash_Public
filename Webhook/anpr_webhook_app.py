from flask import Flask, request
from werkzeug.utils import secure_filename
from PIL import Image
from datetime import datetime
from dateutil import parser
import logging
import os
import time
import asyncio
import hmac
import hashlib
import re

from defusedxml import ElementTree as ET

import psycopg2
from psycopg2.pool import SimpleConnectionPool

try:
    import yagmail
except Exception:
    yagmail = None

try:
    from telegram import Bot
except Exception:
    Bot = None

from license_plate_validator import corregir_chapa_detectada

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH_MB", "10")) * 1024 * 1024

ALLOWED_IMAGE_FIELDS = {"licensePlatePicture.jpg", "detectionPicture.jpg"}
ALLOWED_MIMETYPES = {"image/jpeg", "image/png", "image/webp"}

LICENSE_IMAGE_DIR = os.getenv("LICENSE_IMAGE_DIR", "./licenseimage")
DETECTION_IMAGE_DIR = os.getenv("DETECTION_IMAGE_DIR", "./detectionimage")
XML_DIR = os.getenv("XML_DIR", "./xmls")

BASE_URL_FM = os.getenv("BASE_URL_FM", "http://127.0.0.1/").rstrip("/") + "/"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(os.getenv("LOG_FILE", "app.log"))],
)

for d in (LICENSE_IMAGE_DIR, DETECTION_IMAGE_DIR, XML_DIR):
    os.makedirs(d, exist_ok=True)
    try:
        os.chmod(d, 0o750)
    except Exception:
        pass

DB_NAME = os.getenv("DB_NAME", "accesscontrol")
DB_USER = os.getenv("DB_USER", "accesscontrol")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5433"))

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENTS = [e.strip() for e in os.getenv("EMAIL_RECIPIENTS", "").split(",") if e.strip()]

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_IDS = [c.strip() for c in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if c.strip()]

CHATS = {
    "ALERTAS_FM": os.getenv("CHAT_ALERTAS_FM", ""),
    "PORTERIA_FM": os.getenv("CHAT_PORTERIA_FM", ""),
    "OFICINA_FM": os.getenv("CHAT_OFICINA_FM", ""),
    "GENERAL": os.getenv("CHAT_GENERAL", ""),
}

MAX_RETRIES = int(os.getenv("DB_MAX_RETRIES", "5"))
RETRY_INTERVAL = int(os.getenv("DB_RETRY_INTERVAL_SEC", "1"))

db_pool: SimpleConnectionPool | None = None


def init_db_pool():
    global db_pool
    retries = 0
    interval = RETRY_INTERVAL
    while retries < MAX_RETRIES:
        try:
            db_pool = SimpleConnectionPool(
                1,
                10,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
            )
            logging.info("DB connection pool established.")
            return
        except Exception as e:
            logging.error(f"DB pool init error: {e}")
            retries += 1
            if retries < MAX_RETRIES:
                time.sleep(interval)
                interval *= 2
    raise RuntimeError("Failed to initialize DB connection pool after retries.")


init_db_pool()


def get_db_conn():
    if not db_pool:
        raise RuntimeError("DB pool is not initialized")
    return db_pool.getconn()


def put_db_conn(conn):
    if db_pool and conn:
        db_pool.putconn(conn)


def verify_hmac_signature():
    if not WEBHOOK_SECRET:
        return True
    header_sig = request.headers.get("X-Signature", "")
    body = request.get_data()
    expected = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(header_sig, expected):
        logging.warning("Invalid HMAC signature on webhook request.")
        return False
    return True


def sanitize_filename(name: str) -> str:
    fn = secure_filename(name)[:128]
    if not fn:
        fn = f"file_{int(time.time())}"
    return fn


def is_valid_mimetype(file_storage):
    return (file_storage.mimetype or "").lower() in ALLOWED_MIMETYPES


LICENSE_PLATE_REGEX = re.compile(r"^[A-Z0-9\-]{3,12}$", re.IGNORECASE)
DIRECTION_ALLOWED = {"forward", "backward", "unknown"}


def send_email(destinatarios, asunto, mensaje, image_path=None):
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not destinatarios:
        logging.info("Email disabled or not configured.")
        return
    if yagmail is None:
        logging.warning("yagmail not installed; skipping email.")
        return
    try:
        yag = yagmail.SMTP(EMAIL_SENDER, EMAIL_PASSWORD)
        attachments = [image_path] if image_path and os.path.exists(image_path) else []
        yag.send(to=destinatarios, subject=asunto, contents=mensaje, attachments=attachments)
        logging.info("Email sent.")
    except Exception as e:
        logging.error(f"Email send error: {e}")


async def _tg_send(bot: Bot, chat_id: str, text: str, image_path: str | None):
    try:
        if text:
            await bot.send_message(chat_id=chat_id, text=text)
        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                await bot.send_photo(chat_id=chat_id, photo=f)
    except Exception as e:
        logging.error(f"Telegram send error to {chat_id}: {e}")


def send_telegram_alert(text: str, image_path: str | None, chat_ids: list[str]):
    if not TELEGRAM_TOKEN or not chat_ids:
        logging.info("Telegram disabled or no chat ids.")
        return
    if Bot is None:
        logging.warning("python-telegram-bot not installed; skipping Telegram.")
        return

    bot = Bot(token=TELEGRAM_TOKEN)

    async def runner():
        tasks = []
        for cid in chat_ids:
            tasks.append(_tg_send(bot, cid, text, image_path))
        await asyncio.gather(*tasks)

    try:
        asyncio.run(runner())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(runner())


def parse_xml(xml_bytes: bytes, fields: list[str]) -> dict | None:
    try:
        root = ET.fromstring(xml_bytes)
        ns = {'ns': "http://www.hikvision.com/ver20/XMLSchema"}
        data = {}
        for f in fields:
            el = root.find(f".//ns:{f}", ns)
            data[f] = el.text.strip() if (el is not None and el.text) else ""
        return data
    except ET.DefusedXmlException as e:
        logging.error(f"Unsafe XML blocked: {e}")
    except ET.ParseError as e:
        logging.error(f"XML parse error: {e}")
    return None


def save_image_as_webp(file, directory, filename_prefix: str) -> str | None:
    if not file:
        return None
    if not is_valid_mimetype(file):
        logging.warning(f"Rejected file with mimetype {file.mimetype}")
        return None

    os.makedirs(directory, exist_ok=True)

    fn = sanitize_filename(filename_prefix) + ".webp"
    path = os.path.join(directory, fn)

    try:
        img = Image.open(file.stream)
        img.save(path, format="WEBP", quality=85)
        try:
            os.chmod(path, 0o640)
        except Exception:
            pass
        return path
    except Exception as e:
        logging.error(f"Error saving image {fn} -> {e}")
        return None


def insert_detection(cur, values: tuple) -> int | None:
    try:
        cur.execute(
            '''
            INSERT INTO public.lprdetecciones
            ("ipaddress", "eventtype", "licenseplate", "vehicletype", "confidencelevel",
             "direction", "channelname", "licenseimage", "detectionimage", "datatime")
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
            ''',
            values,
        )
        idx = cur.fetchone()[0]
        return idx
    except Exception as e:
        logging.error(f"DB insert error: {e}")
        return None


def is_duplicate(cur, plate: str, when: str, channel: str) -> bool:
    cur.execute(
        '''
        SELECT 1
        FROM public.lprdetecciones
        WHERE licenseplate=%s AND datatime=%s AND channelname=%s
        LIMIT 1
        ''',
        (plate, when, channel),
    )
    return cur.fetchone() is not None


def handle_field_detection(xml_bytes: bytes):
    data = parse_xml(xml_bytes, fields=["eventType"])
    if not data:
        return
    if data.get("eventType", "").lower() == "fielddetection":
        subject = "Alerta persona detectada"
        msg = "Persona detectada dentro del area designada"
        send_telegram_alert(subject + ": " + msg, None, [c for c in TELEGRAM_CHAT_IDS if c])


def handle_license_plate_detection(xml_bytes: bytes, files, cur):
    logging.info("Processing plate detection...")

    data = parse_xml(
        xml_bytes,
        fields=[
            "ipAddress",
            "dateTime",
            "eventType",
            "licensePlate",
            "vehicleType",
            "confidenceLevel",
            "direction",
            "channelName",
        ],
    )
    if not data:
        logging.error("XML missing required fields.")
        return

    plate_raw = (data.get("licensePlate") or "").strip()
    plate = corregir_chapa_detectada(plate_raw, cur) if plate_raw else plate_raw
    if not LICENSE_PLATE_REGEX.match(plate or ""):
        logging.warning(f"Invalid license plate format: {plate!r}")
        plate = (plate or "UNKNOWN")[:12]

    direction = (data.get("direction") or "").lower()
    if direction not in DIRECTION_ALLOWED:
        direction = "unknown"

    channel = (data.get("channelName") or "channel").replace(" ", "_")
    dt_raw = data.get("dateTime") or datetime.utcnow().isoformat()
    try:
        dt = parser.parse(dt_raw)
        dt_str = dt.strftime("%Y-%m-%d_%H-%M-%S")
    except Exception:
        dt_str = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")

    prefix = f"{channel}_{dt_str}"

    license_img_path = save_image_as_webp(
        files.get("licensePlatePicture.jpg"),
        LICENSE_IMAGE_DIR,
        f"{prefix}_license",
    )
    detection_img_path = save_image_as_webp(
        files.get("detectionPicture.jpg"),
        DETECTION_IMAGE_DIR,
        f"{prefix}_detection",
    )

    if is_duplicate(cur, plate, data.get("dateTime"), data.get("channelName")):
        logging.info(f"Duplicate ignored: {plate} @ {data.get('dateTime')} // {data.get('channelName')}")
        return

    registrado = False
    empresa = "Sin empresa asignada"
    comentario = "N/A"
    try:
        cur.execute(
            'SELECT descripcion_movil, chapa, empresa.nombre as empresa_movil, observacion '
            'FROM moviles_movil LEFT JOIN empresa ON empresa.id = empresa_movil_id'
        )
        for descripcion_movil, chapa, empresa_movil, observacion in cur.fetchall():
            if (chapa or "").strip().upper() == (plate or "").strip().upper():
                registrado = True
                data["vehicleType"] = descripcion_movil or data.get("vehicleType")
                empresa = empresa_movil or empresa
                comentario = observacion or comentario
                break
    except Exception as e:
        logging.warning(f"Vehicle enrichment skipped: {e}")

    send_to_telegram = direction == "forward"

    idx = insert_detection(
        cur,
        (
            data.get("ipAddress"),
            data.get("eventType"),
            plate,
            data.get("vehicleType"),
            int((data.get("confidenceLevel") or "0").split(".")[0] or 0),
            direction,
            data.get("channelName"),
            license_img_path or "N/A",
            detection_img_path or "N/A",
            data.get("dateTime"),
        ),
    )
    if idx is None:
        return

    movement_label = {
        "forward": "ingreso",
        "backward": "egreso",
        "unknown": "movimiento",
    }.get(direction, "movimiento")
    msg = f"{empresa} con chapa {plate}, {movement_label} registrado. Comentario: {comentario}"
    check_url = f"{BASE_URL_FM}movil-check-unico/{idx}"

    chat_ids = [c for c in [CHATS.get("ALERTAS_FM"), CHATS.get("PORTERIA_FM"), CHATS.get("OFICINA_FM")] if c]
    if not chat_ids:
        chat_ids = TELEGRAM_CHAT_IDS or ([CHATS.get("GENERAL")] if CHATS.get("GENERAL") else [])

    if send_to_telegram:
        porteria = CHATS.get("PORTERIA_FM") or (TELEGRAM_CHAT_IDS[0] if TELEGRAM_CHAT_IDS else None)
        if porteria:
            send_telegram_alert(
                f"Deteccion {'correcta y registrada' if registrado else 'no registrada o incorrecta'}. {msg} Revisar: {check_url}",
                detection_img_path,
                [porteria],
            )
        send_telegram_alert("Alerta vehiculo: " + msg, detection_img_path, chat_ids)


@app.route("/webhookcallback", methods=["POST"])
def webhook_callback():
    if not verify_hmac_signature():
        return "Invalid signature", 401

    xml_file = request.files.get("anpr.xml")
    xml_field = request.files.get("fielddetection.xml")

    if not xml_file and not xml_field:
        logging.warning("No XML file provided.")
        return "Bad request", 400

    conn = None
    cur = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()

        if xml_field:
            handle_field_detection(xml_field.read())

        if xml_file:
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            xml_path = os.path.join(XML_DIR, f"anpr_{ts}.xml")
            with open(xml_path, "wb") as xf:
                xf.write(xml_file.read())
            with open(xml_path, "rb") as xf:
                handle_license_plate_detection(xf.read(), request.files, cur)

        conn.commit()
        return "OK", 200

    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Webhook error: {e}")
        return "Internal error", 500

    finally:
        if cur:
            cur.close()
        if conn:
            put_db_conn(conn)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("FLASK_PORT", "5000")))
