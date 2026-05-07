import aiohttp
import ssl
import logging
from typing import Optional

async def download_captcha(url: str) -> Optional[bytes]:
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.read()
                else:
                    logging.error(f"Ошибка капчи: {resp.status}")
                    return None
    except Exception as e:
        logging.error(f"Ошибка скачивания капчи: {e}")
        return None