import discord
import os
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput, Select

departments = {
    "Asset": ["Asset"],
    "Security": ["Security Staff", "Exfiltration Heavy Weapons", "Exfiltration Demolition", "Exfiltration"],
    "Finance & Logistics": ["Logistics ", "Logistics Maintenance", "Logistics Cargo"],
    "Technical": ["Engineer", "Designer", "Skunkworks"],
    "Marketing": ["Communication", "Communication: propaganda"],
    "Intelligence": ["IT", "Hygiene", "Culinary"],
    "Staff": ["HR"]
}

class Induction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        print("Induction:cog loaded")

    async def log_position(self, message: str):
        channel = self.bot.get_channel(os.getenv("LOG_CHANNEL_ID"))
        if channel:
            await channel.send(message)

    @app_commands.command(name="traxus", description="Start the onboarding process")
    async def traxus(self, interaction: discord.Interaction):
        # Using this to prevent interaction timeouts
        # noinspection PyUnresolvedReferences
        await interaction.response.defer(ephemeral=True)

        # Check if user has the exclusion role
        if any(role.id == os.getenv("ONBOARDING_EXCLUSION_ROLE") for role in interaction.user.roles):
            await interaction.followup.send(
                "# Already onboarded.",
                ephemeral=True)
            return True

        view = OnboardingView(interaction.user)
        await interaction.followup.send(
            content="# Welcome, Valued Asset, to TRAXUS Industries. Please select your desired department below",
            view=view,
            ephemeral=True
        )


# Onboarding classes
class OnboardingView(View):
    def __init__(self, member):
        super().__init__(timeout=300)
        self.member = member
        self.department = None
        self.job = None
        self.add_item(DepartmentSelect(self))


class DepartmentSelect(Select):
    def __init__(self, parent_view):
        options = [discord.SelectOption(label=dept) for dept in departments.keys()]
        super().__init__(placeholder="Choose your department.", options=options)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        self.parent_view.department = self.values[0]
        await interaction.followup.send(
            f"# **{self.parent_view.department}** Department selected. Now pick a job.",
            ephemeral=True,
            view=JobView(self.parent_view)
        )


class JobView(View):
    def __init__(self, parent_view):
        super().__init__(timeout=300)
        self.parent_view = parent_view
        self.add_item(JobSelect(parent_view))
        self.add_item(SubmitButton(parent_view))


class JobSelect(Select):
    def __init__(self, parent_view):
        options = [discord.SelectOption(label=job) for job in departments[parent_view.department]]
        super().__init__(placeholder="Choose your job.", options=options)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.job = self.values[0]
        await interaction.response.defer(ephemeral=True)


class SubmitButton(Button):
    def __init__(self, parent_view):
        super().__init__(label="Submit", style=discord.ButtonStyle.success)
        self.parent_view = parent_view


    async def callback(self, interaction: discord.Interaction):
        member = self.parent_view.member
        department = self.parent_view.department
        job = self.parent_view.job

        channel: discord.TextChannel = interaction.guild.get_channel(int(os.getenv("APPROVAL_CHANNEL_ID")))
        if not department or not job:
            await interaction.response.send_message(
                "❗ Please complete all selections before submitting.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="New Role Request",
            description=f"**User:** {member.mention}\n**Department:** {department}\n**Job:** {job}",
            color=discord.Color.blue()
        )

        await channel.send(embed=embed, view=ApprovalView(member, department, job))

        log_channel = interaction.guild.get_channel(int(os.getenv("LOG_CHANNEL_ID")))
        if log_channel:
            await log_channel.send(f"📥 {member.mention} applied for {department} - {job}")

        await interaction.response.send_message(
            "Your request has been submitted for approval!",
            ephemeral=True
        )


# Approval
class ApprovalView(View):
    def __init__(self, member, department, job):
        super().__init__(timeout=None)
        self.member = member
        self.department = department
        self.job = job
        self.add_item(ApproveButton(self))
        self.add_item(RejectButton(self))


class ApproveButton(Button):
    def __init__(self, parent):
        super().__init__(label="Approve ✅", style=discord.ButtonStyle.success)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        if not any(role.id == int(os.getenv("APPROVER_ROLE_ID")) for role in interaction.user.roles):
            await interaction.followup.send("You are not authorized...", ephemeral=True)
            return True

        try:
            await self.parent.member.send(
                f"✅ Your role as **{self.parent.job}** in **{self.parent.department}** has been approved!"
            )
        except discord.Forbidden:
            pass

        full_nick = f"{self.parent.member.display_name} | TRAXUS {self.parent.job}"
        short_nick = f"TRAXUS {self.parent.job}"
        final_nick = full_nick if len(full_nick) <= 32 else short_nick

        try:
            await self.parent.member.edit(nick=final_nick)
        except discord.Forbidden:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "⚠️ I don't have permission to change the user's nickname.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "⚠️ I don't have permission to change the user's nickname.", ephemeral=True
                )
        except Exception as e:
            await interaction.followup.send(
                f" Failed to change nickname: {e}", ephemeral=True
            )

        log_channel = interaction.guild.get_channel(int(os.getenv("LOG_CHANNEL_ID")))
        if log_channel:
            await log_channel.send(f"✅ Application approved by {interaction.user.mention} for {self.parent.member.mention}")

        await interaction.response.defer(thinking=False)

        await interaction.message.edit(view=None, content="✅ Application approved.")
        if not interaction.response.is_done():
            await interaction.response.send_message("✅ Application approved.", ephemeral=True)
        else:
            await interaction.followup.send("✅ Application approved.", ephemeral=True)

        # Alter existing embed for ACCEPTED status
        interaction.message.embeds[0].set_footer(text=f"✅ Application approved.")
        print(f"{interaction.message.embeds[0]}")

    # Rejection


class RejectButton(Button):
    def __init__(self, parent):
        super().__init__(label="Reject ❌", style=discord.ButtonStyle.danger)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        if not any(role.id == int(os.getenv("APPROVER_ROLE_ID")) for role in interaction.user.roles):
            await interaction.response.send_message(f"You are not authorized...", ephemeral=True)
            return True

        await interaction.response.send_modal(RejectReasonModal(self.parent, interaction.user))


class RejectReasonModal(Modal, title="Rejection Reason"):
    def __init__(self, parent, approver):
        super().__init__()
        self.parent = parent
        self.approver = approver
        self.reason = TextInput(label="Reason", style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await self.parent.member.send(
                f"❌ Your application for **{self.parent.job}** in **{self.parent.department}** "
                f"has been rejected.\n**Reason:** {self.reason.value}"
            )
        except discord.Forbidden:
            pass

        log_channel = interaction.guild.get_channel(int(os.getenv("LOG_CHANNEL_ID")))
        if log_channel:
            await log_channel.send(
                f"❌ Application rejected by {self.approver.mention} for {self.parent.member.mention} — Reason: {self.reason.value}"
            )

        await interaction.response.defer(thinking=False)
        await interaction.message.edit(view=None, content="❌ Application rejected.")

        # Alter existing embed for REJECTED status
        interaction.message.embeds[0].set_footer(text=f"❌ Application rejected. {self.reason.value}")
        print(f"{interaction.message.embeds[0]}")


async def setup(bot):
    await bot.add_cog(Induction(bot))
