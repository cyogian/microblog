import json
import requests
from flask_babel import _
from app import app

def translate(text, src_lang, dest_lang):
    if "TRANSLATOR_KEY" not in app.config or not app.config["TRANSLATOR_KEY"]:
        return _('Error: the translation service is not configured.')
    
    key = app.config["TRANSLATOR_KEY"]
    lang = f"{src_lang}-{dest_lang}"
    r = requests.get(f"https://translate.yandex.net/api/v1.5/tr.json/translate?key={key}&text={text}&lang={lang}")

    if r.status_code != 200:
        return _('Error: the translation service failed.')
    return json.loads(r.content.decode('utf-8-sig'))
