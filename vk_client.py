import os
import ssl
import urllib3
import requests
from vk_api import VkApi
from typing import Tuple, Optional, Union

# ---------- Отключение SSL ----------
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

_custom_session = requests.Session()
_custom_session.verify = False

def patch_vk_session(vk: VkApi):
    if hasattr(vk, 'http') and hasattr(vk.http, '_session'):
        vk.http._session = _custom_session
    if hasattr(vk, 'session'):
        vk.session = _custom_session

def create_vk_session(phone: str, password: str = '') -> VkApi:
    vk = VkApi(login=phone, password=password)
    patch_vk_session(vk)
    return vk

# ---------- Авторизация по SMS-коду ----------
def request_code(phone: str) -> Tuple[bool, Optional[VkApi], Optional[Union[str, dict]], Optional[bytes]]:
    vk = create_vk_session(phone, password='')
    try:
        vk.auth()
        return False, None, "Неожиданная успешная авторизация", None
    except Exception as e:
        # Капча
        if hasattr(e, 'captcha_sid') and hasattr(e, 'captcha_img'):
            return False, vk, {"sid": e.captcha_sid, "img_url": e.captcha_img}, None
        # Требуется код подтверждения
        if hasattr(e, 'need_validation') and e.need_validation:
            return True, vk, None, None
        err_str = str(e).lower()
        if "validation" in err_str or "code" in err_str:
            return True, vk, None, None
        # Flood control
        if "flood" in err_str or "too many requests" in err_str:
            return False, None, "⚠️ Слишком много запросов. Подождите 10-15 минут и попробуйте снова.", None
        if "captcha" in err_str:
            return False, vk, "Требуется капча, но данные не найдены. Попробуйте позже.", None
        # Остальные ошибки
        return False, None, f"❌ Ошибка VK: {e}", None

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
            return False, None, "❌ Неверный код подтверждения. Попробуйте ещё раз."
        if "flood" in err_str or "too many" in err_str:
            return False, None, "⚠️ Слишком много попыток. Подождите 10 минут."
        return False, None, f"❌ Ошибка: {e}"

# ---------- Авторизация по паролю ----------
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
        err_str = str(e).lower()
        if "password" in err_str or "login" in err_str or "invalid" in err_str:
            if "password" in err_str:
                return False, None, "❌ Неверный пароль. Попробуйте ещё раз."
            return False, None, "❌ Неверный логин или пароль."
        if "flood" in err_str or "too many" in err_str:
            return False, None, "⚠️ Слишком много попыток входа. Подождите 15 минут."
        if "captcha" in err_str:
            return False, None, "Требуется капча, но данные не загрузились. Попробуйте позже."
        return False, None, f"❌ Ошибка: {e}"