import datetime
import discord
import asyncio
import apis.nexus as nexus
from main import Barry
from utils.interface import EasyView, EasyButton

class WhitelistedManagement:
    def __init__(self, bot: Barry):
        self.bot = bot

    async def start_application(self, user: discord.User) -> None:
        embed = discord.Embed(
            title="☆ Compton Whitelisted",
            description="""
            Thank you for your interest in joining us!

            Compton Whitelisted is an __application only__ version of our public server, with the addition of several whitelisted-only perks & content! There will be __no__ unranked units and __minimal__ fail roleplay in this server, so if you're looking for an escape from that, whitelisted is for you!

            I'll be guiding you through the application process, detailing everything you should know before submitting your application. Press Continue!
            """,
            color=self.bot.primary_embed_color
        )

        continue_view = EasyView(
            children=[
                EasyButton(
                    label="Continue with Application",
                    style=discord.ButtonStyle.green,
                    emoji="📒"
                )
            ],
            user_id=user.id,
            disable_after_good_interaction=True
        )

        await user.send(embed=embed, view=continue_view)

        if await continue_view.wait():
            return
        
        try:
            rblx = await self.bot.nexus_api_client.query(type=nexus.SubjectType.Discord(), sub=user.id)
        except nexus.NotFound:
            await user.send("Please verify your Roblox account with me, then retry. (/verify)")
            return
                
        member = self.bot.get_guild(900141799992078397).get_member(user.id)
        if not member:
            await user.send("You must be a member of our main server to apply for whitelisted. discord.gg/crp2")
            return
        
        if not member.joined_at or not member.joined_at - datetime.timedelta(days=14):
            await user.send("You are too new.")

        response = {
            "Why do you want to join whitelisted?": None,
            "Are you able to be in a Discord VC when in-game?": None,
            "Will you be able to contribute to the server?\n-# Will you be able to participate in our sessions every weekend, join departments, and follow our rules?": None
        }

        async def get_response(question: str, time: int):
            embed = discord.Embed(
                description=question,
                color=self.bot.pending_embed_color
            ).set_footer(text=f"Respond within {time} seconds!")
            
            prompt = await user.send(embed=embed)

            def check(m):
                return m.author.id == user.id and m.channel.id == user.dm_channel.id
            
            msg = await self.bot.wait_for('message', check=check, timeout=time)

            response[question] = msg

        if not user.dm_channel:
            await user.create_dm()

        try:
            await get_response("Why do you want to join whitelisted?", time=10)
            await get_response("Are you able to be in a Discord VC when in-game?", time=10)
            await get_response("Will you be able to contribute to the server?\n-# Will you be able to participate in our sessions every weekend, join departments, and follow our rules?", time=10)
        except asyncio.TimeoutError:
            await user.send("The application timed out! Feel free to retry below.", view=TestApp())
            return
        
        embed = discord.Embed(
            title="Application"
        )
        
        await user.send(content="Your application has been submitted, hope to see you soon!")

class TestApp(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Go", custom_id="temp")
    async def go(self, i, b):
        await i.response.defer()
        await i.client.whitelisted.start_application(i.user)