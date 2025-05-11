import discord
import asyncio
import typing
import time

from main import Barry

class missing: pass
MISSING = missing()

async def handle_timeout(interaction, view, msg = None, silent: bool = False):
    timed_out = await view.wait()
    if timed_out:
        if not silent:
            await interaction.client.view_timed_out(interaction, msg)
        return True
    return False

class Reload(discord.ui.View):
    def __init__(self, user_id: int, func: typing.Coroutine, args: set):
        super().__init__(timeout=600)
        self.user_id = user_id
        self.func = func
        self.args = args

        self.message = None
        
        self.lock = asyncio.Lock()
        self.busy = False

        self._max_uses = 10
        self._uses = 0
        self._disable_for = 3

    async def on_timeout(self):
        await self._disable(keep_disabled=True)
    
    async def _disable(self, keep_disabled: bool = False):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                await self._change_item(("disabled", True), item)
        else:
            await self.message.edit(view=self)

        if not keep_disabled:
            await asyncio.sleep(self._disable_for)

            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    await self._change_item(("disabled", False), item)
            else:
                await self.message.edit(view=self)
            
            self.busy = False

    async def _change_item(self, args, item: discord.Component):
        url = getattr(item, "url")
        if not url:
            setattr(item, *args)

    async def interaction_check(self, interaction: discord.Interaction[Barry]):
        if not self.message:
            return await interaction.response.defer()
        
        if interaction.user.id == self.user_id:
            if self._uses >= self._max_uses:
                await self._disable(keep_disabled=True)
                return await interaction.client.view_exhausted(interaction)
            return True
        else:
            await interaction.client.missing_permissions_prompt(interaction)
            return False
        
    @discord.ui.button(label="Refresh", emoji="<:Refresh:1315207851475603497>")
    async def refresh(self, interaction: discord.Interaction[Barry], button: discord.ui.Button):
        if self.busy:
            return await interaction.response.defer()
        
        async with self.lock:
            self.busy = True

            await self.func(interaction, True)
            self._uses += 1

            await self._disable()
            self.busy = False

class JoinServer(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Join Server", url="https://policeroleplay.community/join/crp")

class EasyView(discord.ui.View):
    def __init__(self, *, children, timeout: int = 300, interaction: discord.Interaction = None, user_id: int = None, disable_after_good_interaction: bool = False):
        super().__init__(timeout=timeout)

        self.add_children(*children)

        self.interaction = interaction

        self.user_id = user_id
        
        self.disable_after_good_interaction = disable_after_good_interaction

    def add_children(self, *children):
        for child in children:
            self.add_item(child)
        
        return self

    async def _edit_message(self, interaction: discord.Interaction[Barry]):
        if not interaction.is_expired():
            try:
                if interaction.response.is_done():
                    await interaction.edit_original_response(view=self)
                else:
                    await interaction.response.edit_message(view=self)
            except:
                pass

    async def _disable(self, enable_in: int = 0, interaction: discord.Interaction[Barry] = None, exclude_buttons: tuple = None):        
        for item in self.children:
            if exclude_buttons:
                if type(item) in exclude_buttons:
                    continue
            item.disabled = True

        if interaction:
            await self._edit_message(interaction)

        if enable_in:
            await asyncio.sleep(enable_in)
            await self._enable()

        return self

    async def _enable(self, interaction: discord.Interaction[Barry] = None, *exclude_buttons: tuple):
        if self.is_finished():
            return
        
        for item in self.children:
            if exclude_buttons:
                if item not in exclude_buttons:
                    continue
            item.disabled = False

        if interaction:
            await self._edit_message(interaction)

        return self

    async def on_timeout(self):
        if not self.interaction:
            return
        await self._disable(interaction=self.interaction)
            
    async def interaction_check(self, interaction):        
        if self.user_id:
            if interaction.user.id != self.user_id:
                await interaction.client.missing_permissions_prompt(interaction)
                return False
        
        if self.disable_after_good_interaction:
            self.stop()

        return True
        
class Continue(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Continue")

    async def callback(self, interaction: discord.Interaction[Barry]):
        await interaction.response.defer()
        self.view.stop()

class Cancel(discord.ui.Button):
    def __init__(self, func, args):
        super().__init__(label="Cancel", style=discord.ButtonStyle.red)
        self.func = func
        self.args = args
    
    async def interaction_check(self, interaction):
        setattr(self.view, "cancelled", True)
        return True

    async def callback(self, interaction: discord.Interaction[Barry]):
        await interaction.response.defer()
        await self.func(*self.args)
        self.view.stop()

class EasyModal(discord.ui.Modal):
    def __init__(self, title: str, inputs: dict, timeout: int = 600, stop_on_submit: bool = False):
        super().__init__(title=title, timeout=timeout)
        
        self.data: typing.Dict[discord.ui.TextInput] = MISSING

        self.stop_on_submit = stop_on_submit

        for input in inputs:
            self.add_item(input)

    async def on_submit(self, interaction: discord.Interaction[Barry]):
        await interaction.response.defer()
        
        data = {}

        for item in self.children:
            if isinstance(item, discord.ui.TextInput):
                data.update({item.custom_id: item})

        self.data = data

        if self.stop_on_submit:
            self.stop()

class EasyButton(discord.ui.Button):
    def __init__(self, func: callable = None, label: str = None, emoji: str = None, style: discord.ButtonStyle = discord.ButtonStyle.grey, disabled: bool = False, cooldown: int = 0, *args, **kwargs):
        super().__init__(
            label=label,
            emoji=emoji,
            style=style,
            disabled=disabled
        )

        self.cooldown = cooldown

        self.func = func
        self.args = args
        self.kwargs = kwargs

        if cooldown:
            self._cooldown_activated = asyncio.Event()

    async def _disable(self, interaction: discord.Interaction, keep_disabled: bool = False):
        if not interaction.response.is_done():
            await interaction.response.defer()
        
        if self.view is None:
            return
        
        for item in self.view.children:
            if isinstance(item, discord.ui.Button):
                await self._change_item(("disabled", True), item)
        else:
            try:
                await interaction.edit_original_response(view=self.view)
            except:
                pass
                
        self._cooldown_activated.set()

        if not keep_disabled:
            await asyncio.sleep(self.cooldown)

            self._cooldown_activated.clear()

            if self.view is None:
                return

            if not self.view.is_finished():
                for item in self.view.children:
                    if isinstance(item, discord.ui.Button):
                        await self._change_item(("disabled", False), item)
                else:
                    try:
                        await interaction.edit_original_response(view=self.view)
                    except:
                        pass

    async def _change_item(self, args, item: discord.Component):
        url = getattr(item, "url")
        if not url:
            setattr(item, *args)

    async def callback(self, interaction: discord.Interaction[Barry]):
        if self.cooldown:
            asyncio.create_task(self._disable(interaction))
            await self._cooldown_activated.wait()

        if self.func:
            await self.func(*self.args, _interaction=interaction, **self.kwargs)
        else:
            await interaction.response.defer()

class EasySelect(discord.ui.Select):
    def __init__(self, placeholder: str, options: list[discord.SelectOption], func):
        super().__init__(
            placeholder=placeholder,
            options=options
        )

        self.func = func

    async def callback(self, interaction: discord.Interaction[Barry]):
        await self.func(_interaction=interaction, selected=self.values[0])

class RestrictionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Handle", custom_id="handle_alert")
    async def handle(self, interaction: discord.Interaction[Barry], button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        restriction = await interaction.client.game_alerts_db.execute("SELECT * FROM alerts WHERE message = ?", (interaction.message.id,))
        restriction = await restriction.fetchone()

        if not restriction:
            await interaction.followup.send(
                content="Alert not found.",
                ephemeral=True
            )
            return
        
        async with interaction.client.game_alerts_lock:
            await interaction.client.game_alerts_db.execute("INSERT INTO logs (id, user, time) VALUES (?, ?, ?)", (restriction['id'], interaction.user.id, time.time()))
            await interaction.client.game_alerts_db.commit()

        await interaction.followup.delete_message(interaction.message.id)

        await interaction.followup.send(
            content="Handled",
            ephemeral=True
        )

class FastPassManager:
    def __init__(self, client: Barry):
        self.client = client

    async def start_fast_pass(self, interaction: discord.Interaction[Barry]):
        if 1356619481123651695 in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message(content="You've already fast-passed into the team!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)

        async def start_form(_interaction):
            modal = EasyModal(
                title="Fast-Pass Form",
                inputs=[
                    discord.ui.TextInput(
                        label="Why do you want to be a janitor?",
                        custom_id="whyyyyyyyyy"
                    )
                ],
                stop_on_submit=True
            )
            await _interaction.response.send_modal(modal)
            timed_out = await modal.wait()
            if timed_out:
                return
            
            why = modal.data['whyyyyyyyyy'].value
            
            async def user_selected(_interaction, selected):
                if selected == "Berry":
                    await _interaction.response.send_message(content="No.", ephemeral=True)
                else:
                    await _interaction.response.edit_message(content="Correct! 😊", embed=None, view=None)
                    if 1356619481123651695 not in [role.id for role in _interaction.user.roles]:
                        await interaction.user.add_roles(interaction.client.get_guild(900141799992078397).get_role(1356619481123651695)); print(1)
                    await _interaction.followup.send("Welcome to the team!", ephemeral=True)
                    await interaction.client.get_channel(1356620030057386095).send(f"Welcome to the team, {interaction.user.mention}!")
                    embed = discord.Embed(
                title="Janitor Pass",
                description=f"{interaction.user.mention} wants to be a janitor because `{why}`. Pass given!"
            )
                    await interaction.client.get_channel(1185788966113378424).send(embed=embed)
                    
            dropdown = EasySelect(
                placeholder="Select the user",
                options=[
                    *(discord.SelectOption(
                        label="Barry" + ("‎" * _)
                    ) for _ in range(20)),
                    discord.SelectOption(
                        label="Berry"
                    )
                ],
                func=user_selected
            )
            view = EasyView(
                children=[dropdown]
            )
            embed = discord.Embed(
                title="Staff Fast-Pass",
                description="**Final question:** Out of the list of users below, who is the best?"
            )
            await _interaction.edit_original_response(embed=embed, view=view)
            if await view.wait():
                return

        view = EasyView(
            children=[
                EasyButton(
                    func=start_form,
                    label="Start"
                )
            ],
            disable_after_good_interaction=True
        )
        embed = discord.Embed(
            title="Janitor Fast-Pass",
            description="We are glad to see that you are interested in a janitor fast-pass.\n\nPlease fill out our form, and the pass will be yours!"
        )
        await interaction.followup.send(
            embed=embed,
            view=view,
            ephemeral=True
        )
        
class ApplyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Become a janitor!", custom_id="getstartedfastpass-")
    async def callback(self, i, b):
        await i.client.fastpass.start_fast_pass(i)