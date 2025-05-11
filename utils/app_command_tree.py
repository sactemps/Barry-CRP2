import datetime
import discord
import asyncio
import random

from discord import app_commands
from discord.ext import commands
from apis.prc.models.exceptions import ApiException

class AppCommandTree(discord.app_commands.CommandTree):
    def __init__(self, client):
        super().__init__(client=client)

    async def interaction_check(self, interaction: discord.Interaction):
        asyncio.create_task(interaction.client.log_slash_command(interaction))
                
        return True
    
    async def on_error(self, interaction: discord.Interaction, error):        
        data = {
            "content": None,
            "embed": None,
            "view": None
        }

        if isinstance(error, (app_commands.Cooldown, app_commands.CommandOnCooldown)):
            data = {
                "content": f"<:x2:1218517627450687509> **{interaction.user.name}**, this command is on cooldown. Try again <t:{int((datetime.datetime.now() + datetime.timedelta(seconds=error.retry_after)).timestamp())}:R>.",
                "delete_after": error.retry_after
            }
            await self._respond(interaction, data)
            return
        
        elif isinstance(error, app_commands.CommandNotFound):
            data = {"content": "<:x2:1218517627450687509> I am currently **starting** - commands are unavailable."}
            await self._respond(interaction, data)
            return
        
        elif isinstance(error, app_commands.errors.CommandInvokeError):
            original = error.__cause__
            if isinstance(original, ApiException):
                data = {"content": "<:x2:1218517627450687509> An error occurred while communicating with PRC.", "view": None, "embed": None}
                await self._respond(interaction, data)
                return
            
            elif isinstance(original, TimeoutError):
                data = {"content": "<:x2:1218517627450687509> **Timed out**, please repeat your action.", "embed": None, "view": None}
                await self._respond(interaction, data)
                return
            
        elif isinstance(error, (app_commands.errors.MissingPermissions, app_commands.errors.MissingAnyRole, app_commands.errors.MissingRole, commands.errors.MissingAnyRole, commands.errors.MissingRole, commands.errors.MissingPermissions)):
            data = {"content": "<:x2:1218517627450687509> You are not allowed to use this command.", "view": None, "embed": None}
            await self._respond(interaction, data)
            return
        
        error_id = await interaction.client.log_error(error, __file__, 'app-command')
        data = {"content": f"<:x2:1218517627450687509> An error occurred, please retry your action.\n-# ID: {error_id}", "embed": None, "view": None}
        
        await self._respond(interaction, data)

    async def _respond(self, interaction, data):
        if interaction.is_expired():
            return
        
        if interaction.response.is_done():
            await interaction.edit_original_response(**data)
        else:
            await interaction.response.send_message(**data)