import asyncio
import hashlib
import aiofiles
import aiohttp
# ... (other imports and settings like FETCH_RETRIES_COUNT, HEADERS, etc.)

class ConfigWorker: # (or whatever the class name is in your script)
    def __init__(self, number, url, cfg_file_path, ghapi, info):
        self._number = number
        self._url = url
        self._cfg_file_path = cfg_file_path
        self._ghapi = ghapi
        self._info = info

    async def is_equal_urls_config(self, new_data: str) -> bool:
        old_data, new_data = b"", new_data.encode()
        try:
            async with aiofiles.open(self._cfg_file_path, "r", encoding="utf-8") as file:
                old_data = (await file.read()).encode()
        except FileNotFoundError:
            pass
        except:
            logger.exception(f"{self._number} | Compare configs data unexpected error")
        else:
            return hashlib.md5(old_data).hexdigest() == hashlib.md5(new_data).hexdigest()
        return False

    async def download_and_save(self) -> dict:
        try:
            data = await self.fetch_data()
        except Exception:
            logger.exception(f"Number {self._number} | config fetching error")
            return self._info

        if data is None:
            return self._info

        try:
            if not (await self.is_equal_urls_config(data)):
                await self._ghapi.update_or_create_file(
                    self._cfg_file_path,
                    msg=f"🚀 Updating config file 📁 {self._cfg_file_path}",
                    content=data,
                )
                logger.info(f"📁 {self._number} | Config saved successfully {self._cfg_file_path}")

                self._info = self.get_or_create_info(info=self._info, force=True)
        except Exception:
            logger.exception(f"Number {self._number} | writing to file error")

        return self._info

    async def fetch_data(self) -> None | str:
        async with aiohttp.ClientSession() as session:
            for retry in range(FETCH_RETRIES_COUNT):
                resp = None
                try:
                    resp = await session.request(method=HTTPMethod.GET, url=self._url, headers=HEADERS)
                    resp.raise_for_status()
                    return (await resp.read()).decode(encoding="cp437")
                except Exception as e:
                    status = getattr(resp, "status", "N/A")
                    logger.warning(
                        f"Retry #{retry} | URL {self._url} error: {e} (status: {status}). Sleeping..."
                    )

                await asyncio.sleep(RETRY_TIMEOUT)
        return None
