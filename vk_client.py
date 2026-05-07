import os
import ssl
import urllib3
import requests
from vk_api import VkApi
from typing import Tuple, Optional, Union

# --- Отключение SSL глобально ---
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Подмена SSL-контекста по умолчанию
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Создаём сессию без проверки
_custom_session = requests.Session()
_custom_session.verify = False

# Патчим класс VkApi: подменяем его внутреннюю сессию после инициализации
_original_vk_init = VkApi.__init__

def _patched_vk_init(self, *args, **kwargs):
    _original_vk_init(self, *args, **kwargs)
    if hasattr(self, 'http') and hasattr(self.http, '_session'):
        self.http._session = _custom_session
    # Также некоторые версии используют session
    if hasattr(self, 'session'):
        self.session = _custom_session

VkApi.__init__ = _patched_vk_init

def create_vk_session(phone: str, password: str = '') -> VkApi:
    return VkApi(login=phone, password=password)

# ---------- Вход по SMS-коду ----------
def request_code(phone: str) -> Tuple[bool, Optional[VkApi], Optional[Union[str, dict]], Optional[bytes]]:
    vk = create_vk_session(phone, password='')
    try:
        vk.auth()
        return False, None, "Неожиданная успешная авторизация", None
    except Exception as e:
        if hasattr(e, 'captcha_sid') and hasattr(e, 'captcha_img'):
            return False, vk, {"sid": e.captcha_sid, "img_url": e.captcha_img}, None
        if hasattr(e, 'need_validation') and e.need_validation:
            return True, vk, None, None
        err_str = str(e).lower()
        if "validation" in err_str or "code" in err_str:
            return True, vk, None, None
        return False, None, str(e), None

def submit_code(vk: VkApi, code: str, captcha_sid: str = None, captcha_key: str = None) -> Tuple[bool, Optional[str], Optional[Union[str, dict]]]:
    try:
        if captcha_sid and captcha_key:
            vk.auth(auth_code=code, captcha_sid=captcha_sid, captcha_key=captcha_key)
        else:
            vk.auth(auth_code=code)
        token = vk.token['access_token']
        return True, token, None
    except Exception as e:
        if hasattr(e, 'captcha_sid') and hasattr(e, 'captcha_img'):
            return False, None, {"sid": e.captcha_sid, "img_url": e.captcha_img}
        err_str = str(e).lower()
        if "code" in err_str or "invalid" in err_str:
            return False, None, "Неверный код подтверждения. Попробуйте ещё раз."
        return False, None, str(e)

# ---------- Вход по паролю ----------
def login_with_password(phone: str, password: str, captcha_sid: str = None, captcha_key: str = None) -> Tuple[bool, Optional[str], Optional[str]]:
    try:
        vk = create_vk_session(phone, password)
        if captcha_sid and captcha_key:
            vk.auth(captcha_sid=captcha_sid, captcha_key=captcha_key)
        else:
            vk.auth()
        token = vk.token['access_token']
        return True, token, None
    except Exception as e:
        if hasattr(e, 'captcha_sid') and hasattr(e, 'captcha_img'):
            return False, None, f"captcha_needed:{e.captcha_sid}:{e.captcha_img}"
        return False, None, str(e)