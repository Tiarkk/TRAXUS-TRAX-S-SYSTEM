import discord
import logging
import os
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput, Select

########## These can be updated to match current structure

departments = {
    "Asset": ["Asset"],
    "Security": ["Security Staff", "Exfiltration Heavy Weapons", "Exfiltration Demolition", "Exfiltration"],
    "Finance & Logistics": ["Logistics ", "Logistics Maintenance", "Logistics Cargo"],
    "Technical": ["Engineer", "Designer", "Skunkworks"],
    "Marketing": ["Communication", "Communication: propaganda"],
    "Intelligence": ["IT", "Hygiene", "Culinary"],
    "Staff": ["HR"]
}

shorter_departments = {
    "Asset": {
        1: ["Asset"],
        2: ["Asset"],
        3: ["Asset"]
    },
    "Security": {
        1: ["Security Staff", "Exfiltration Heavy Weapons", "Exfiltration Demolition", "Exfiltration"],
        2: ["Sec Staff", "Exfil H/Weapons", "Exfil Demo", "Exfil"],
        3: ["Sec Stf", "Exf HW", "Exf Demo", "Exf"]
    },
    "Finance & Logistics": {
        1: ["Logistics", "Logistics Maintenance", "Logistics Cargo"],
        2: ["Logs", "Logs Mnt", "Logs Cargo"],
        3: ["Lg", "Lg Mnt", "Lg C"],
    },
    "Technical": {
        1: ["Engineer", "Designer", "Skunkworks"],
        2: ["Eng", "Designer", "SkunkWks"],
        3: ["Eng", "Dsgnr", "Skwks"]
    },
    "Marketing": {
        1: ["Communication", "Communication: Propaganda"],
        2: ["Comms", "Comms: Props"],
        3: ["Cms", "Cms: Prp"]
    },
    "Intelligence": {
        1: ["IT", "Hygiene", "Culinary"],
        2: ["IT", "Hyg", "Cul"],
        3: ["IT", "Hyg", "Cul"]
    },
    "Staff": {
        1: ["HR"],
        2: ["HR"],
        3: ["HR"]
    }
}

class Induction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = logging.getLogger('discord')
        self.logger.setLevel(logging.INFO)

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
                contents="# Already onboarded.",
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
            await interaction.followup.send(content="You are not authorized...", ephemeral=True)
            return True

        # Nickname Assignment goes here :)
        full_nick = f"{self.parent.member.display_name} | TRAXUS {self.parent.job}"

        if len(full_nick) <= 32:
            # proceed
            final_nick = full_nick
        else:
            short_name_dict = shorter_departments[self.parent.department]
            name_index = short_name_dict[1].index(self.parent.job)

            final_nick = f"TRAXUS {self.parent.job}"

            # Iterate through shorter names to see one that fits
            # Otherwise default to "TRAXUS {job}"
            for i in range(1,4):
                if len(f"{self.parent.member.display_name} | TRAXUS {short_name_dict[i][name_index]}") <= 32:
                    final_nick = f"{self.parent.member.display_name} | TRAXUS {short_name_dict[i][name_index]}"
                    print(f"{self.parent.member.display_name} | TRAXUS {short_name_dict[i][name_index]} is a suitable size")
                    break
                else:
                    print(f"{short_name_dict[i][name_index]} was too long, trying next one")

        # Edit member nickname
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

        if final_nick == f"TRAXUS {self.parent.job}":  # name was too long
            print("Username too long, defaulting to TRAXUS {job}")

            # Send confirmation message - nickname change was unsuccessful - using default pattern")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "✅ Application approved.\n**⚠️ Nickname was too long - Will need adjustment**", ephemeral=True)
            else:
                await interaction.followup.send(
                    "✅ Application approved.\n**⚠️ Nickname was too long - Will need adjustment**", ephemeral=True)

            log_channel = interaction.guild.get_channel(int(os.getenv("LOG_CHANNEL_ID")))
            if log_channel:
                await log_channel.send(
                    f"✅ Application approved by {interaction.user.mention} for {self.parent.member.mention}\n**⚠️ Nickname was too long - Will need adjustment**")

        else:
            # Send confirmation message - nickname change was successful
            await interaction.message.edit(view=None, content="✅ Application approved.")
            if not interaction.response.is_done():
                await interaction.response.send_message("✅ Application approved.", ephemeral=True)
            else:
                await interaction.followup.send("✅ Application approved.", ephemeral=True)

            log_channel = interaction.guild.get_channel(int(os.getenv("LOG_CHANNEL_ID")))
            if log_channel:
                await log_channel.send(
                    f"✅ Application approved by {interaction.user.mention} for {self.parent.member.mention}")

        # Send applicant a DM
        try:
            await self.parent.member.send(
                f"✅ Your role as **{self.parent.job}** in **{self.parent.department}** has been approved!"
            )
        except discord.Forbidden:
            pass

        # Alter existing embed for ACCEPTED status
        interaction.message.embeds[0].set_footer(text=f"✅ Application approved.")
        print(f"{interaction.message.embeds[0].footer.text}")


class RejectButton(Button):
    def __init__(self, parent):
        super().__init__(label="Reject ❌", style=discord.ButtonStyle.danger)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        if not any(role.id == int(os.getenv("APPROVER_ROLE_ID")) for role in interaction.user.roles):
            await interaction.response.send_message(f"You are not authorized...", ephemeral=True)
            return True

        await interaction.response.send_message(modal=RejectReasonModal(self.parent, interaction.user))


class RejectReasonModal(Modal, title="Rejection Reason"):
    def __init__(self, parent, approver):
        super().__init__()
        self.parent = parent
        self.approver = approver
        self.reason = TextInput(label="Reason", style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
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


        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Application rejected.", ephemeral=True)
        else:
            await interaction.followup.send(content="❌ Application rejected.", ephemeral=True)

        await interaction.message.edit(view=None, content="❌ Application rejected.")
        # Alter existing embed for REJECTED status
        interaction.message.embeds[0].set_footer(text=f"❌ Application rejected. {self.reason.value}")
        print(f"{interaction.message.embeds[0].footer.text}")


async def setup(bot):
    await bot.add_cog(Induction(bot))
