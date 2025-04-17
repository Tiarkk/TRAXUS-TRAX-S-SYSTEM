# define imports of course :)

import logging
import discord
from discord import app_commands
from discord.ext import commands


# Class setup - This is where you define the Cog
class Example(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # Reference to the main bot instance - REQUIRED!

        # Logging setup - Can be moved to global by defining these outside the class if needed ^^^
        self.logger = logging.getLogger('discord')
        self.logger.setLevel(logging.INFO)

    # You need this to load the Cog into the bot during it's setup
    async def cog_load(self):
        print("Induction:cog loaded")


    # This is where you define the commands for this Cog
    @app_commands.command(name="test", description="I'm an example command")
    async def test_command(self, interaction: discord.Interaction):
        """Example command to test this Cog"""
        await interaction.response.send_message("This is a test command!", ephemeral=True)

        # Log the command execution - can be customized to log more details
        # such as the command name, user ID, etc.
        self.logger.info(f"Test command executed by {interaction.user.name} in {interaction.channel.name}")


# This is to let the bot set up the Cog - it won't work without this
async def setup(bot):
    await bot.add_cog(Example(bot))  #  Make sure you add the Cog "name" to the bot - i.e. Example