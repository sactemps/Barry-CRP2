import typing

from nexus.types import Account
from main import Barry

class RobloxVerification:
    def __init__(self, bot: Barry):
        self.bot = bot

    async def fetch_verification(self, discord_user_id: int = None, roblox_user_name: str = None, roblox_user_id: int = None, return_raw: bool = False) -> typing.Union[Account, dict]:
        params = {"discord_user_id", "roblox_user_name", "roblox_user_id"}
        arg = {}

        for k, v in locals().items():
            if k not in params:
                continue

            if k in arg:
                raise TypeError("one keyword argument should be passed, not multiple")
            
            if v:
                arg.update({k: v})
        
        verification = await self.bot.roblox_verification_db.execute(
            f"SELECT * FROM verified_users WHERE {arg.keys()[0]} = ?",
            (arg.values()[0])
        )
        verification = await verification.fetchall()

        if not verification:
            return None
        
        if return_raw:
            return verification
        else:
            return [Account(d) for d in verification]
