import json as j
import datetime
import aiohttp
import asyncio
import time

from apis.roblox.types import RateLimited, RequestFailed
from discord.ext import tasks
from main import Barry

class Roblox:
    def __init__(self, bot: Barry):
        self.bot = bot

        self.session: aiohttp.ClientSession = bot.session
        
        self.lock: asyncio.Lock = bot.roblox_lock
        
        self.responses = []
        self.cached_responses = []

        self.cache = {}

        self.log_api_responses.start()
        self.log_caching_responses.start()

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

                await self.bot.roblox_api_db.execute(
                    "INSERT INTO api_responses (endpoint, status, json, epoch_timestamp, datetime) VALUES (?, ?, ?, ?, ?)",
                    (*payload,)
                )
                await self.bot.roblox_api_db.commit()

    @tasks.loop(seconds=5)
    async def log_caching_responses(self):
        if not self.cached_responses:
            return
        
        async with self.lock:
            cached_responses = self.cached_responses.copy()
            self.cached_responses.clear()

            for response in cached_responses:
                endpoint = response.get("endpoint")
                json = response.get("json")
                epoch_timestamp = response.get("epoch_timestamp")
                _datetime = datetime.datetime.now(datetime.UTC)

                payload = (
                    endpoint,
                    json,
                    epoch_timestamp,
                    _datetime
                )

                await self.bot.roblox_api_db.execute(
                    "INSERT INTO cache_returned (endpoint, json, epoch_timestamp, datetime) VALUES (?, ?, ?, ?)",
                    (*payload,)
                )
                await self.bot.roblox_api_db.commit()

    async def get(self, endpoint, retries: int = 10, method: str = "GET", json: dict = None):
        payload = {
            "url": endpoint,
            "method": method
        }

        if json:
            payload.update({"json": json})

        async with self.lock:
            for i in range(retries):
                key = f"{method}:{endpoint}:{json}"

                cached = self.cache.get(key)
                if cached:
                    _response = {
                        "endpoint": endpoint,
                        "json": j.dumps(cached["json"]),
                        "epoch_timestamp": time.time()
                    }
                    self.cached_responses.append(_response)
                    return cached["json"]
                
                async with self.bot.session.request(**payload) as response:
                    json = await response.json()
                    
                    try:
                        response.raise_for_status()

                        self.cache.update(
                            {
                                key: {
                                    "json": json
                                }
                            }
                        )

                        _response = {
                            "endpoint": endpoint,
                            "json": j.dumps(json),
                            "epoch_timestamp": time.time(),
                            "status": response.status
                        }
                        self.responses.append(_response)
                        
                        return json
                    except aiohttp.ClientResponseError as response_error:
                        status = response_error.status

                        try:
                            json = await response.json()
                        except:
                            json = {"message": "Valid JSON not returned"}

                        _response = {
                            "endpoint": endpoint,
                            "json": j.dumps(json),
                            "epoch_timestamp": time.time(),
                            "status": response.status
                        }
                        self.responses.append(_response)

                        if status == 429:
                            await asyncio.sleep(0.5 + i / 2)
                        else:
                            raise RequestFailed()
            else:
                raise RateLimited()

    async def fetch_roblox_information(self, username: str = None, id: str = None):
        if not id and not username:
            raise TypeError("missing id or usernane")
        
        if not username and id:
            username = await self.fetch_roblox_username(id=id)

        if not id and username:
            id = await self.fetch_roblox_id(username=username)

        url = f"https://users.roblox.com/v1/users/{id}"

        data = await self.get(endpoint=url)
        return data
        
    async def fetch_roblox_username(self, id: str):
        url = f"https://users.roblox.com/v1/users/{id}"
        
        username = await self.get(endpoint=url)
        username = username.get("name")
        return username
                
    async def fetch_roblox_id(self, username: str):
        url = f"https://users.roblox.com/v1/usernames/users"
        
        payload = {
            "usernames": [username],
            "excludeBannedUsers": False
        }

        roblox_id = await self.get(endpoint=url, json=payload, method="POST")
        roblox_id = roblox_id.get("data", {"MISSING": {"id": ""}})[0]["id"]
        return roblox_id
    
    async def fetch_headshot(self, id: str):
        size = 150

        url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={id}&size={size}x{size}&format=Png&isCircular=false&thumbnailType=HeadShot"
        
        response = await self.get(endpoint=url)
        return response["data"][0]['imageUrl']