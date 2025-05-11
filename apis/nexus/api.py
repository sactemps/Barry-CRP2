import json as j

import asyncio
import aiohttp
import typing
import time

from discord.ext import tasks
from apis.nexus.types import *

url_nexus = None # 5/11/2025: Temp until Nexus is restored

class NexusApi:
    def __init__(self, session: aiohttp.ClientSession, key, bot):
        self.session = session
        
        self.responses = []
        self.lock = asyncio.Lock()

        self.bot = bot

        self._key = key
        
        self._retries = 3

        self.log_api_responses.start()

    @property
    def headers(self):
        return {
            "Authorization": self._key,
            "User-Agent": "Barry",
            "Content-Type": "application/json"
        }

    def nexus_response_error(self, status: int, code: int, message: str):
        codes = {
            400: BadRequest,
            401: Unauthorized,
            403: Forbidden,
            404: NotFound,
            405: MethodNotAllowed,
            409: Conflict,
            413: PayloadTooLarge,
            500: InternalServerError
        }

        if message is None:
            "Message manually set. The provided message was None."

        raise codes.get(status, InternalServerError)(code, message)
    
    @tasks.loop(seconds=5)
    async def log_api_responses(self):
        if not self.responses:
            return
        
        async with self.lock:
            responses = self.responses.copy()
            self.responses.clear()

            for response in responses:
                endpoint = response.get("endpoint")
                status = response.get("status")
                json = response.get("json")
                epoch_timestamp = response.get("epoch_timestamp")
                _datetime = datetime.datetime.now(datetime.UTC)

                payload = (
                    endpoint,
                    status,
                    json,
                    epoch_timestamp,
                    _datetime
                )

                await self.bot.nexus_api_db.execute(
                    "INSERT INTO api_responses (endpoint, status, json, epoch_timestamp, datetime) VALUES (?, ?, ?, ?, ?)",
                    payload
                )
                await self.bot.nexus_api_db.commit()

    async def start_session(self, type: typing.Union[SubjectType.Roblox, SubjectType.Discord], sub) -> Session:
        async with self.session.get(
            url_nexus + f'/init?type={type}&sub={sub}',
            headers=self.headers
        ) as response:
            try:
                response.raise_for_status()
            except aiohttp.ClientResponseError:
                try:
                    json = await response.json()
                except:
                    json = {"code": 0, "message": "Message unavailable - JSON body not returned by Nexus."}
                raise self.nexus_response_error(response.status, json["code"], json["message"])

            json = await response.json()

            _url = json.get("url")
            _expires_at = json.get("expiresAt")

            return Session(
                url=_url,
                expires_at=_expires_at
            )
            
    async def query(self, type: SubjectType, sub):        
        endpoint = f"/query?type={type}&sub={sub}"
        async with self.session.get(
            url_nexus + endpoint,
            headers=self.headers
        ) as response:
            try:
                json = await response.json()
            except:
                json = {"code": 0, "message": f"Message unavailable - JSON body not returned by Nexus OR it was malformed. Response code: {response.status}"}

            _response = {
                "endpoint": endpoint,
                "json": j.dumps(json),
                "epoch_timestamp": time.time(),
                "status": response.status
            }
            self.responses.append(_response)

            try:
                response.raise_for_status()
                if json.get('code'):
                    raise Exception()
            except aiohttp.ClientResponseError:
                raise self.nexus_response_error(response.status, json.get("code"), json.get("message"))

            return Account(json)