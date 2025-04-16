import discord
import asyncio
from discord.ext import commands
import os
from aiohttp import ClientSession
# from dotenv import load_dotenv

# load_dotenv() - Use for local testing (without Docker)

class TRAX(commands.Bot):
    def __init__(
            self,
            *args,
            initial_extensions: list[str],
            web_client: ClientSession,
            **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.web_client = web_client
        self.initial_extensions = initial_extensions

        self.env_TOKEN = os.getenv('TOKEN')
        self.env_BOT_CHANNEL_ID=int(os.getenv("BOT_CHANNEL_ID"))
        self.env_GUILD_ID=int(os.getenv("GUILD_ID"))
        self.env_APPROVAL_CHANNEL_ID=int(os.getenv("APPROVAL_CHANNEL_ID"))
        self.env_ONBOARDING_EXCLUSION_ROLE=int(os.getenv("ONBOARDING_EXCLUSION_ROLE_ID"))
        self.env_APPROVER_ROLE_ID = int(os.getenv("APPROVER_ROLE_ID"))
        self.env_LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

    async def on_ready(self):
        print(f'Bot is online as {self.user}')

        channel = self.get_channel(self.env_BOT_CHANNEL_ID)
        if channel:
            await channel.send("# `TRAXUS TRAX-S SYSTEM IS NOW ONLINE`")

    async def setup_hook(self) -> None:
        for extension in self.initial_extensions:
            await self.load_extension(extension)
        try:
            guild = discord.Object(self.env_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f"Synced commands: {[cmd.name for cmd in synced]}")
        except Exception as e:
            print(f"Failed to sync commands: {e}")


async def main():
    async with ClientSession() as our_client:
        extensions = ["cogs.induction"]
        async with TRAX(
                command_prefix=commands.when_mentioned,
                case_insensitive=True,
                web_client=our_client,
                initial_extensions=extensions,
                intents=discord.Intents.all(),
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name="TRAXUS profits rise",
                    url="https://traxus.global"),
                status=discord.Status.online) as bot:
            await bot.start(bot.env_TOKEN)


asyncio.run(main())
