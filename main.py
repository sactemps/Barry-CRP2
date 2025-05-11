import chat_exporter
import aiosqlite
import datetime
import asyncio
import discord
import aiohttp
import base64
import random
import json
import time
import sys
import io
import os

from utils.app_command_tree import AppCommandTree

from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()

class CommandTree(app_commands.CommandTree):
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        with open('data/utils/blacklisted.json', 'r') as file:
            blacklisted = json.load(file)
        if interaction.user.id in blacklisted:
            await interaction.response.send_message('You are blacklisted.')
            return False
        return True
    
class Barry(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("b!"),
            intents=discord.Intents.all(),
            help_command=None,
            tree_cls=AppCommandTree
        )

        self.erlc_api_key = os.getenv("KEY_ERLC_API")
        self.nexus_api_key = os.getenv("KEY_NEXUS_API")

        self.remove_command('help')
        self.add_check(self.is_not_blacklisted)
        
        self.primary_embed_color = discord.Colour.from_str(os.getenv("HEX_PRIMARY_COLOR"))
        self.pending_embed_color = discord.Colour.from_str(os.getenv("HEX_PENDING_COLOR"))
        self.accepted_hex = discord.Colour.from_str(os.getenv("HEX_ACCEPTED"))
        self.denied_hex = discord.Colour.from_str(os.getenv("HEX_DENIED"))
        self.warning_embed_color = discord.Colour.brand_red()
        
        self.crp_icon = "https://cdn.discordapp.com/attachments/1337273846167765044/1337278411571335199/Compton_Roleplay_2_Logo_Base.png?ex=67a6dd12&is=67a58b92&hm=6001a4df53a6a18d876ba8b512f7f788e86c826fc919efc5716caa61262746c7&"

        self.gamenights_reaction_role_lock = asyncio.Lock()
        self.roblox_verification_lock = asyncio.Lock()
        self.interactions_lock = asyncio.Lock()
        self.game_alerts_lock = asyncio.Lock()
        self.reports_lock = asyncio.Lock()
        self.errors_lock = asyncio.Lock()
        self.roblox_lock = asyncio.Lock()
        self.lock = asyncio.Lock()

        self.player_check_bypass = [
            "maso_ie", "CandyMan7293", "ButternutCAD"
        ]

        self.error_messages = [
            "Oops! We hit a snag.",
            "Uh-oh! Something's not quite right.",
            "Whoops! We encountered an issue.",
            "Yikes! There was a hiccup.",
            "Oh no! We're having trouble.",
            "Darn it! Something went awry.",
            "Oopsie! We ran into a problem.",
            "Uh-oh! We're experiencing difficulties.",
            "Yikes! We hit a bump in the road.",
            "Oh dear! We're facing an issue."
        ]
                
    async def send_online_message(self):
        channel = self.get_channel(1185788966113378424)
        await channel.send("Online")
	
    async def is_not_blacklisted(self, ctx):
        with open('data/utils/blacklisted.json', 'r') as file:
            blacklisted = json.load(file)
        return ctx.author.id not in blacklisted
    
    async def setup_hook(self):
        self.interactions_db = await aiosqlite.connect('./data/discord/interactions.db')
        await self.interactions_db.execute("CREATE TABLE IF NOT EXISTS interactions (user_id, data, epoch_timestamp, datetime)")
        await self.interactions_db.commit()
        
        self.command_usage_db = await aiosqlite.connect('./data/discord/command_usage.db')
        await self.command_usage_db.execute("CREATE TABLE IF NOT EXISTS prefix_commands (user_id, command_name, command_message_content, command_channel_id, command_guild_id, epoch_timestamp, datetime)")
        await self.command_usage_db.commit()
        await self.command_usage_db.execute("CREATE TABLE IF NOT EXISTS slash_commands (user_id, command_name, command_data, command_channel_id, command_guild_id, epoch_timestamp, datetime)")
        await self.command_usage_db.commit()

        self.reports_db = await aiosqlite.connect('./data/utils/reports.db')
        self.reports_db.row_factory = aiosqlite.Row
        await self.reports_db.execute("CREATE TABLE IF NOT EXISTS reports (id, user_id, type, subtype, outcome, reported_party, reason, evidence, claimed_by, report_message_id, report_thread_id, report_channel_id, handler, handler_note, submitted_on_datetime, submitted_on_epoch, handled_on_datetime, handled_on_epoch)")
        await self.reports_db.commit()

        self.errors_db = await aiosqlite.connect('./data/utils/errors.db')
        self.errors_db.row_factory = aiosqlite.Row
        await self.errors_db.execute("CREATE TABLE IF NOT EXISTS errors (id, type, path, exc, tb_lineno, datetime)")
        await self.errors_db.commit()

        self.gamenights_reaction_role_db = await aiosqlite.connect('./data/utils/reaction_roles.db')
        self.gamenights_reaction_role_db.row_factory = aiosqlite.Row
        await self.gamenights_reaction_role_db.execute("CREATE TABLE IF NOT EXISTS reaction_roles (message_id, emoji, created_by)")
        await self.gamenights_reaction_role_db.commit()

        self.roblox_verification_db = await aiosqlite.connect('./data/utils/roblox_verification.db')
        self.roblox_verification_db.row_factory = aiosqlite.Row
        await self.roblox_verification_db.execute("CREATE TABLE IF NOT EXISTS verified_users (discord, roblox_username, roblox_user_id, linked_on_epoch_timestamp, linked_on_datetime, expired)")
        await self.roblox_verification_db.commit()

        self.roblox_api_db = await aiosqlite.connect('./data/apis/roblox_api.db')
        await self.roblox_api_db.execute("CREATE TABLE IF NOT EXISTS api_responses (endpoint, status, json, epoch_timestamp, datetime)")
        await self.roblox_api_db.commit()
        await self.roblox_api_db.execute("CREATE TABLE IF NOT EXISTS cache_returned (endpoint, json, epoch_timestamp, datetime)")
        await self.roblox_api_db.commit()

        self.nexus_api_db = await aiosqlite.connect('./data/apis/nexus_api.db')
        await self.nexus_api_db.execute("CREATE TABLE IF NOT EXISTS api_responses (endpoint, json, status, epoch_timestamp, datetime)")
        await self.nexus_api_db.commit()
        await self.nexus_api_db.execute("CREATE TABLE IF NOT EXISTS cache_returned (endpoint, json, epoch_timestamp, datetime)")
        await self.nexus_api_db.commit()

        self.prc_api_db = await aiosqlite.connect('./data/apis/prc_api.db')
        await self.prc_api_db.execute("CREATE TABLE IF NOT EXISTS api_responses (endpoint, status, json, epoch_timestamp, datetime)")
        await self.prc_api_db.commit()
        await self.prc_api_db.execute("CREATE TABLE IF NOT EXISTS cache_returned (endpoint, json, epoch_timestamp, datetime)")
        await self.prc_api_db.commit()

        self.game_alerts_db = await aiosqlite.connect('./data/utils/game_alerts.db')
        self.game_alerts_db.row_factory = aiosqlite.Row
        await self.game_alerts_db.execute("CREATE TABLE IF NOT EXISTS alerts (id, type, player, message, time)")
        await self.game_alerts_db.execute("CREATE TABLE IF NOT EXISTS logs (id, user, time)")
        await self.game_alerts_db.commit()

        self.trial_mod_db = await aiosqlite.connect('./data/utils/trial_mod.db')
        self.trial_mod_db.row_factory = aiosqlite.Row
        await self.trial_mod_db.execute("CREATE TABLE IF NOT EXISTS trial_mods (id, mentor, timezone)")
        await self.trial_mod_db.commit()

        self.session = aiohttp.ClientSession()

        from modules.support.reports.interface.hq import ReportAdminView
        self.add_view(ReportAdminView())

        from apis.nexus.api import NexusApi
        self.nexus_api_client = NexusApi(self.session, self.nexus_api_key, self)

        from apis.prc.api import ErlcApi
        self.erlc_api_client = ErlcApi(self)

        from apis.roblox.api import Roblox
        self.roblox_api_client = Roblox(self)

        from utils.whitelisted_application import WhitelistedManagement, TestApp
        self.whitelisted = WhitelistedManagement(self)
        self.add_view(TestApp())

        from utils.interface import FastPassManager, ApplyButton
        self.fastpass = FastPassManager(self)
        self.add_view(ApplyButton())

    async def on_ready(self):
        await self.loader()
        
        print("Online")
        try:
            await self.send_online_message()
        except Exception as e:
            print("⚠️   Could not send online message: ", e)

        from modules.support.support_select import SupportSelectView

        from modules.support.appeals.hq import AppealView
        from modules.support.faq.select import FAQDropdownView
        from modules.utilities.staff_handbook import StaffView
        from utils.interface import RestrictionView
        
        self.add_view(RestrictionView())
        self.add_view(SupportSelectView())
        self.add_view(AppealView())
        self.add_view(FAQDropdownView())
        self.add_view(StaffView())

        await self.load_extension("jishaku")

    async def close(self):
        print("Close triggered")

        databases = [
            self.errors_db, self.prc_api_db, self.reports_db,
            self.nexus_api_db, self.roblox_api_db, self.interactions_db,
            self.command_usage_db, self.roblox_verification_db, self.gamenights_reaction_role_db,
            self.game_alerts_db, self.trial_mod_db
        ]

        async def close_database(db: aiosqlite.Connection):
            try:
                if db is None or db._running is False:
                    return
                for i in range(5):
                    if i == 4:
                        print(f"Rolling back db {db.name} | {i}")
                        try:
                            await db.rollback()
                        except Exception as e:
                            print(f"Failed to rollback {db.name}: {e}")
                    if db.in_transaction:
                        print(f"In transaction db {db.name} | {i}")
                        await asyncio.sleep(0.1 * (2 ** i))
                    else:
                        break
                print(f"Closing db {db.name}")
                try:
                    await db.close()
                except Exception as e:
                    print(f"Failed to close {db.name}: {e}")
            except Exception as e:
                print(f"Failed to close {db}: {e}")

        await asyncio.gather(*(close_database(db) for db in databases))

        print("Closing client session")
        try:
            if not self.session.closed:
                self.session.detach()
                await self.session.close()
        except Exception as e:
            print(f"Failed to close client session: {e}")

        print("Running super().close()")

        await super().close()

    async def loader(self):
        """ONLY RUN WHEN LOADING COGS!!!!!!!!!!"""
        print(" \n-----------------------------LOADING COGS-----------------------------")
        for file in Path('cogs').glob('**/*.py'):
            *tree, _ = file.parts
            cog_name = f"{'.'.join(tree)}.{file.stem}"
            module = __import__(cog_name, fromlist=["setup"], level=0)
            try:
                if hasattr(module, "setup"):
                    await self.load_extension(cog_name)
                    print(f"🛬  Cog {cog_name} loaded")
                else:
                    print(f"⏭️  Ignoring {cog_name} as it doesn't have a setup function")
            except Exception as e:
                print(f"⚠️  Caught exception while loading extension {cog_name}: {e}")
        print("-----------------------------COGS LOADED-----------------------------\n ")

    async def unloader(self):
        """ONLY RUN WHEN UNLOADING COGS!!!!!!!!!!"""
        print(" \n-----------------------------UNLOADING COGS-----------------------------")
        for ext in list(self.extensions):
            try:
                await self.unload_extension(ext)
                print(f"🛫  Cog {ext} unloaded")
            except Exception as e:
                print(f"⚠️  Caught exception while unloading extension {ext}: {e}")
        print("-----------------------------COGS UNLOADED-----------------------------\n ")

    async def _respond_to_handler(self, handler: discord.Interaction | commands.Context, **payload):
        if isinstance(handler, discord.Interaction):
            if handler.response.is_done():
                return await handler.edit_original_response(**payload)
            await handler.response.send_message(**payload)
        elif isinstance(handler, commands.Context):
            await handler.reply(**payload)

    async def view_exhausted(self, handler: discord.Interaction | commands.Context):
        embed = discord.Embed(
            title="View Exhausted",
            description="This view is exhausted.",
            color=self.warning_embed_color
        )

        await self._respond_to_handler(handler, **{"embed": embed})

    async def account_verified(self, handler: discord.Interaction | commands.Context):
        embed = discord.Embed(
            title="Roblox Account Verified",
            description="Your account has been verified! Contact support to make any adjustments.",
            color=self.warning_embed_color
        ).set_footer(
            text=handler.guild.name,
            icon_url=self.crp_icon
        )

        await self._respond_to_handler(handler, **{"embed": embed, "view": None})
    
    async def appeal_created(self, handler: discord.Interaction | commands.Context, ref: str):
        embed = discord.Embed(
            title="Appeal Created",
            description="Your appeal has been submitted for review.",
            color=self.primary_embed_color
        ).set_footer(
            text=f"ref. {ref}"
        )

        await self._respond_to_handler(handler, **{"embed": embed})
    
    async def missing_permissions_prompt(self, handler: discord.Interaction | commands.Context):
        embed = discord.Embed(
            title="Missing Permissions",
            description="You are not allowed to perform this action.",
            color=self.warning_embed_color
        )

        data = {"embed": embed}
        if isinstance(handler, discord.Interaction):
            data.update({"ephemeral": True})

        await self._respond_to_handler(handler, **data)

    async def log_slash_command(self, interaction: discord.Interaction):
        command = interaction.command

        async with self.lock:
            payload = (
                interaction.user.id,
                None if not command else command.name,
                json.dumps(interaction.data),
                interaction.channel.id,
                None if not interaction.guild else interaction.guild.id,
                time.time(),
                datetime.datetime.now(datetime.UTC)
            )

            await self.command_usage_db.execute(
                "INSERT INTO slash_commands (user_id, command_name, command_data, command_channel_id, command_guild_id, epoch_timestamp, datetime) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (*payload,)
            )
            await self.command_usage_db.commit()

    async def create_roblox_verification(self, discord, roblox_username, roblox_id):
        data = (
            discord,
            roblox_username,
            roblox_id,
            datetime.datetime.now(datetime.UTC),
            time.time()
        )

        expire_previous_verification = False
        already_verified = await self.roblox_verification_db.execute("SELECT * FROM verified_users WHERE discord = ? AND expired IS NULL", (discord,))
        if already_verified:
            expire_previous_verification = True

        async with self.roblox_verification_lock:
            if expire_previous_verification:
                await self.roblox_verification_db.execute("UPDATE verified_users SET expired = ? WHERE discord = ?", (True, discord))
                await self.roblox_verification_db.commit()
            await self.roblox_verification_db.execute("INSERT INTO verified_users (discord, roblox_username, roblox_user_id, linked_on_datetime, linked_on_epoch_timestamp) VALUES (?, ?, ?, ?, ?)", data)
            await self.roblox_verification_db.commit()

    async def log_error(self, exception: Exception, file, type: str):
        try:
            random_bytes = os.urandom(6)
            short_id = base64.urlsafe_b64encode(random_bytes).rstrip(b'=').decode('utf-8')
            
            async with self.errors_lock:
                await self.errors_db.execute(
                    "INSERT INTO errors (id, type, path, exc, tb_lineno, datetime) VALUES (?, ?, ?, ?, ?, ?)",
                    (str(short_id), type, file, str(exception), exception.__traceback__.tb_lineno, str(datetime.datetime.now()))
                )
                await self.errors_db.commit()

            return short_id
        except Exception as e:
            print(f"⚠️   Failed to log error: {e} at line {e.__traceback__.tb_lineno}")

    async def on_interaction(self, interaction: discord.Interaction):
        async with self.interactions_lock:
            user_id = getattr(interaction.user, "id", None)
            data = getattr(interaction, "data", {})

            payload = (
                user_id,
                json.dumps(data),
                time.time(),
                str(interaction.created_at)
            )

            await self.interactions_db.execute(
                "INSERT INTO interactions (user_id, data, epoch_timestamp, datetime) VALUES (?, ?, ?, ?)",
                (*payload,)
            )
            await self.interactions_db.commit()
            
    async def on_command(self, ctx: commands.Context):
        async with self.lock:
            payload = (
                ctx.author.id,
                ctx.command.name,
                ctx.message.content,
                ctx.channel.id,
                None if not ctx.guild else ctx.guild.id,
                time.time(),
                datetime.datetime.now(datetime.UTC)
            )

            await self.command_usage_db.execute(
                "INSERT INTO prefix_commands (user_id, command_name, command_message_content, command_channel_id, command_guild_id, epoch_timestamp, datetime) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (*payload,)
            )
            await self.command_usage_db.commit()

    async def view_timed_out(self, handler: discord.Interaction, msg: discord.Message | discord.WebhookMessage = None):
        if not isinstance(handler, discord.Interaction):
            raise TypeError(f"type {type(handler)} is not supported")
        
        embed = discord.Embed(
            title="Prompt Timeout",
            description="This prompt has timed-out, and can no longer be used.\n-# Feel free to repeat this action again.",
            color=self.warning_embed_color
        )

        pl = {
            "view": None,
            "content": None,
            "attachments": [],
            "embed": embed
        }

        if msg:
            await msg.edit(
                embed=embed,
                content=None,
                attachments=[],
                view=None
            )
            return

        await self._respond_to_handler(handler, **pl)

    async def operation_cancelled(self, handler: commands.Context | discord.Interaction):
        embed = discord.Embed(
            title="Operation Cancelled",
            description="The operation has been cancelled.",
            color=self.warning_embed_color
        )

        await self._respond_to_handler(handler, embed=embed, view=None)
        
    async def generate_transcript(self, channel: discord.TextChannel, generated_by: discord.User):
        if not isinstance(channel, discord.TextChannel) or not isinstance(generated_by, (discord.User, discord.Member, int)):
            raise TypeError('Invalid arg')

        transcript = await chat_exporter.export(channel, guild=channel.guild, bot=self)

        if transcript is None:
            print(f"⚠️   Transcript is None for channel {channel.id}")
            return
        
        transcript_file = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"{channel.name}-{channel.id}.html"
        )

        transcript_channel = self.get_partial_messageable(1229566264658362409)
        message = None
        
        try:
            if generated_by is int:
                mention = f"<@{generated_by}>"
            else:
                mention = generated_by.mention

            message = await transcript_channel.send(
                content=f"Transcripted generated by {mention} for `#{channel.name}` `({channel.id})`",
                file=transcript_file,
                allowed_mentions=discord.AllowedMentions.none()
            )
        except Exception as e:
            print(f"⚠️   Failed to send transcript: {e}")
            raise e

        return {"t": transcript_file, "m": message}
    
    async def verification_not_found(self, handler: discord.Interaction | commands.Context):
        embed = discord.Embed(
            title="Account Not Verified",
            description="Your account was not verified. If you believe this is incorrect, try again.",
            color=self.warning_embed_color
        ).set_footer(
            text=handler.guild.name,
            icon_url=self.crp_icon
        )
        await self._respond_to_handler(handler, **{"embed": embed, "view": None})

    async def account_already_verified(self, handler: discord.Interaction | commands.Context):
        embed = discord.Embed(
            title="Already Verified",
            description="Your Roblox account is already verified! Click the button below to reverify.",
            color=self.warning_embed_color
        ).set_footer(
            text=handler.guild.name,
            icon_url=self.crp_icon
        )

        from utils.interface import EasyView, EasyButton
        import apis.nexus as nexus

        async def reverify_account(_interaction: discord.Interaction):
            if not _interaction.response.is_done():
                await _interaction.response.defer(ephemeral=True)

            async def check_verification(_interaction: discord.Interaction[Barry]):
                if not _interaction.response.is_done():
                    await _interaction.response.defer()
                
                try:
                    account = await _interaction.client.nexus_api_client.query(type=nexus.SubjectType.Discord(), sub=_interaction.user.id)
                except nexus.NotFound:
                    await self.verification_not_found(_interaction)
                    return
                except nexus.NexusApiError:
                    embed = discord.Embed(
                        title=random.choice(self.error_messages),
                        description="Something went wrong while communicating with Nexus.",
                        color=_interaction.client.primary_embed_color
                    ).set_footer(
                        text="Compton Roleplay 2",
                        icon_url=self.crp_icon
                    )
                    await _interaction.followup.send(
                        embed=embed, 
                        ephemeral=True
                    )

                view.stop()
                
                await _interaction.client.create_roblox_verification(
                    _interaction.user.id,
                    await _interaction.client.roblox_api_client.fetch_roblox_username(account.roblox_accounts[0].id),
                    account.roblox_accounts[0].id
                )
                
                await _interaction.client.account_verified(_interaction)

            view = EasyView(
                children=[
                    EasyButton(
                        check_verification, label="I have verified"
                    )
                ],
                disable_after_good_interaction=True,
                user_id=_interaction.user.id
            )

            session = await _interaction.client.nexus_api_client.start_session(type=nexus.SubjectType.Discord(), sub=_interaction.user.id)
            
            embed = discord.Embed(
                title="Roblox Verification",
                description=f"Please click [this link]({session.url}) and authorize your Roblox account to continue. Once verified, click the button below.",
                color=_interaction.client.primary_embed_color
            ).set_footer(
                text=_interaction.guild.name,
                icon_url=_interaction.client.crp_icon
            )

            await _interaction.edit_original_response(embed=embed, view=view)

        view = EasyView(
            children=[
                EasyButton(
                    label="Reverify",
                    func=reverify_account
                )
            ],
            user_id=handler.user.id,
            disable_after_good_interaction=True
        )

        await self._respond_to_handler(handler, **{"embed": embed, "view": view})

bot = Barry()

@bot.command(name="blacklist")
async def blacklist(ctx: commands.Context, user: discord.User):
    try:
        if ctx.author.id != 1110370709559062529:
            if "love" in ctx.message.content:
                return await ctx.message.add_reaction("♥️")
            return await ctx.message.add_reaction("❌")

        with open('data/utils/blacklisted.json', 'r') as file:
            data = json.load(file)
        if user.id not in data:
            data.append(user.id)

            with open('data/utils/blacklisted.json', 'w') as file:
                json.dump(data, file, indent=4)

        await ctx.message.add_reaction("✅")
    except Exception as e:
        raise Exception(e)
    
@bot.command(name="unblacklist")
async def blacklist(ctx: commands.Context, user: discord.User):
    try:
        if ctx.author.id != 1110370709559062529:
            return await ctx.message.add_reaction("❌")

        with open('data/utils/blacklisted.json', 'r') as file:
            data = json.load(file)
        if user.id in data:
            del data[data.index(user.id)]

            with open('data/utils/blacklisted.json', 'w') as file:
                json.dump(data, file, indent=4)

        await ctx.message.add_reaction("✅")
    except Exception as e:
        raise Exception(e)
    
@bot.command(name="error")
@commands.is_owner()
async def error(ctx: commands.Context[Barry], error_id: str):
    try:
        async with ctx.bot.errors_db.execute("SELECT * FROM errors WHERE id = ?", (error_id,)) as cur:
            res = await cur.fetchall()
        
        data = list(
            dict(i) for i in res
        )
        
        if len(str(data)) >= 2000:
            await ctx.reply("Result is too long - printing to console")
            print(data)
            return
        
        await ctx.send(data)
    except Exception as e:
        await ctx.reply("An error occurred - printing to console")
        print(e)

@bot.command(name="restart")
@commands.is_owner()
async def restart(ctx: commands.Context[Barry], clear: str = "true"):
    await ctx.send("Restarting")
    if clear == "true":
        os.system("clear")
    os.execv(sys.executable, ['python'] + sys.argv)

@bot.command(name="wlapp")
@commands.is_owner()
async def wlapp(c):
    from utils.whitelisted_application import TestApp
    await c.send(view=TestApp())

@bot.event
async def on_command_error(ctx, e):
    if isinstance(e, commands.CommandNotFound):
        with open('data/utils/blacklisted.json', 'r') as file:
            data = json.load(file)
        if ctx.author.id not in data:
            return
    elif isinstance(e, (commands.MissingPermissions, commands.MissingAnyRole, commands.MissingRole)):
        return
    raise e

@bot.command(name="reload")
@commands.is_owner()
async def reload(ctx: commands.Context[Barry]):
    await ctx.bot.unloader()
    await ctx.bot.loader()
    await ctx.reply("Reloaded")

@bot.tree.command(name="src")
async def src(interaction: discord.Interaction[Barry]):
    await interaction.response.send_message(
	content="Barry is transitioning to be an open-sourced project. This application, and the idea I had when I created it, are the result of inspiration from apps alike. It is *astonishing* how much I've learned from a singular bot that was originally intended to replace Atlas custom commands. Since Barry 2's creation, back in December of 2023, one thing has been clear: do what other applications won't give you.\n\nBy making my project open-source—under MIT license—I hope to inspire and educate those who take interest in applications alike.\n\nThis repository does include everything Barry has—in fact, it's barely touching the surface. Over time, I will add modules and other miscellaneous files until the entire project has been uploaded.\n-# :robot: https://github.com/sactemps/Barry-CRP2",
        ephemeral=True
    )

if __name__ == '__main__':
    TOKEN = os.getenv('BOT_TOKEN')
    bot.run(TOKEN)
