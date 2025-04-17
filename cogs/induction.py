import discord
import logging
import os
import json
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput, Select

# Logging setup
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

########## These can be updated to match current structure

#load deps.,teams and job titles
def load_departments_from_file():
    # Navigate one folder back and locate jobs.json
    filepath = os.path.join(os.path.dirname(__file__), "..", "jobs.json")
    try:
        with open(filepath, "r") as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        print(f"Failed to parse departments from file: {e}")
        return {}
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return {}

# Dictionary defining departments and their respective jobs
departments = load_departments_from_file()

class Induction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        print("Induction:cog loaded")

    @app_commands.command(name="traxus", description="Start the onboarding process")
    async def traxus(self, interaction: discord.Interaction):
        # Using this to prevent interaction timeouts
        # noinspection PyUnresolvedReferences
        await interaction.response.defer(ephemeral=True)

        # Check if user has the exclusion role
        if any(role.id == int(os.getenv("ONBOARDING_EXCLUSION_ROLE_ID")) for role in interaction.user.roles):
            await interaction.followup.send(f"# Already onboarded.")
            return True

        view = OnboardingView(interaction.user)
        await interaction.followup.send(
            content="# Welcome, Valued Asset, to TRAXUS OffWorld Industries. Please select your desired sector below",
            view=view)

    """
    # Command to assign a task based on the user's role
    @bot.tree.command(
        name="task",
        description="Get a task assigned based on your department",
        guild=discord.Object(id=GUILD_ID),
    )
     async def task(interaction: discord.Interaction):
        # Map department names to their corresponding task files
        task_files = {
            "Asset": "tasks/Asset.txt",
            "Security": "tasks/Security.txt",
            "Finance & Logistics": "tasks/Finance & Logistics.txt",
            "Technical": "tasks/Technical.txt",
            "Marketing": "tasks/Marketing.txt",
            "Intelligence": "tasks/Intelligence.txt",
            "Staff": "tasks/Staff.txt",
        }
    
        # Check the user's roles and find a matching department
        for role in interaction.user.roles:
            if role.name in task_files:
                task_file = task_files[role.name]
                try:
                    # Read tasks from the file
                    with open(task_file, "r") as file:
                        tasks = file.readlines()
    
                    with open("tasks/EndTask.txt", "r") as file:
                        end_tasks = file.readlines()
    
                    with open("tasks/Slogans.txt", "r") as file:
                        slogans = file.readlines()
    
                    # Ensure the file is not empty
                    if not tasks:
                        await interaction.response.send_message(
                            f"No tasks available for the {role.name} department. Please contact an admin.",
                            ephemeral=True,
                        )
                        return
    
                    # Assign a random task
                    task = random.choice(tasks).strip()
                    end_tasks = random.choice(end_tasks).strip()
                    slogan = random.choice(slogans).strip()
                    await interaction.response.send_message(
                        f"**{role.name} TASK PROTOCOL ENGAGED**\n"
                        f"> {task}\n\n"
                        f"> {end_tasks}\n\n"
                        f"> {slogan}\n\n"
                        f"**TASK ASSIGNED TO:** {interaction.user.mention}\n"
                    )
                    return
                except FileNotFoundError:
                    await interaction.response.send_message(
                        f"Task file for the {role.name} department is missing. Please contact an admin.",
                        ephemeral=True,
                    )
                    return
    
        # If no matching role is found
        await interaction.response.send_message(
            "You do not have a role associated with any department.", ephemeral=True
        )
    
    """


# View for approving or rejecting role requests
class ApprovalView(View):
    def __init__(self, member, department, team, job):
        super().__init__(timeout=None)
        self.member = member
        self.department = department
        self.team = team
        self.job = job
        self.add_item(ApproveButton(self))
        self.add_item(RejectButton(self))


# Button for approving a role request
class ApproveButton(Button):
    def __init__(self, parent):
        super().__init__(label="Approve ✅", style=discord.ButtonStyle.success)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)

        if not any(role.id == int(os.getenv("APPROVER_ROLE_ID")) for role in interaction.user.roles):
            await interaction.followup.send(content="You are not authorized...")
            return True

        # Nickname Assignment goes here :)
        full_nick = f"{self.parent.member.display_name} | TRAXUS {self.parent.job}"

        if len(full_nick) <= 32:
            # proceed
            final_nick = full_nick
        else:
            short_name_dict = departments[self.parent.department][self.parent.team]
            name_index = short_name_dict["1"].index(self.parent.job)

            final_nick = f"TRAXUS {self.parent.job}"

            # Iterate through shorter names to see one that fits
            # Otherwise default to "TRAXUS {job}"
            for i in range(1,4):
                if len(f"{self.parent.member.display_name} | TRAXUS {short_name_dict[str(i)][name_index]}") <= 32:
                    final_nick = f"{self.parent.member.display_name} | TRAXUS {short_name_dict[str(i)][name_index]}"
                    print(f"{self.parent.member.display_name} | TRAXUS {short_name_dict[str(i)][name_index]} is a suitable size")
                    break
                else:
                    print(f"{short_name_dict[str(i)][name_index]} was too long, trying next one")

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
                    "⚠️ I don't have permission to change the user's nickname.")
        except Exception as e:
            await interaction.followup.send(
                f" Failed to change nickname: {e}")

        if final_nick == f"TRAXUS {self.parent.job}":  # name was too long
            print("Username too long, defaulting to TRAXUS {job}")

            # Send confirmation message - nickname change was unsuccessful - using default pattern")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "✅ Application approved.\n**⚠️ Nickname was too long - Will need adjustment**", ephemeral=True)
            else:
                await interaction.followup.send(
                    content="✅ Application approved.\n**⚠️ Nickname was too long - Will need adjustment**")

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
                await interaction.followup.send("✅ Application approved.")

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


# Button for rejecting a role request
class RejectButton(Button):
    def __init__(self, parent):
        super().__init__(label="Reject ❌", style=discord.ButtonStyle.danger)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        if not any(role.id == int(os.getenv("APPROVER_ROLE_ID")) for role in interaction.user.roles):
            await interaction.response.send_message(f"You are not authorized...", ephemeral=True)
            return True

        await interaction.response.send_modal(RejectReasonModal(self.parent, interaction.user))

# Modal for entering the rejection reason
class RejectReasonModal(Modal, title="Rejection Reason"):
    def __init__(self, parent, approver):
        super().__init__()
        self.parent = parent
        self.approver = approver
        self.reason = TextInput(label="Reason", style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False, ephemeral=True)
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
            await interaction.followup.send(content="❌ Application rejected.")

        await interaction.message.edit(view=None, content="❌ Application rejected.")
        # Alter existing embed for REJECTED status
        interaction.message.embeds[0].set_footer(text=f"❌ Application rejected. {self.reason.value}")
        print(f"{interaction.message.embeds[0].footer.text}")


# View for the onboarding process
class OnboardingView(View):
    def __init__(self, member):
        super().__init__(timeout=300)
        self.member = member
        self.department = None
        self.team = None
        self.job = None
        self.add_item(DepartmentSelect(self))

# Dropdown for selecting a department
class DepartmentSelect(Select):
    def __init__(self, parent_view):
        options = [discord.SelectOption(label=dept) for dept in departments.keys()]
        super().__init__(placeholder="Choose your Sector.", options=options)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.department = self.values[0]
        await interaction.response.send_message(
            f"# **{self.parent_view.department}** Sector selected. Now choose a Department.",
            ephemeral=True,
            view=TeamView(self.parent_view,
            )
        )

# View for selecting a Team
class TeamView(View):
    def __init__(self, parent_view):
        super().__init__(timeout=300)
        self.parent_view = parent_view
        self.add_item(TeamSelect(parent_view))

class TeamSelect(Select):
    def __init__(self, parent_view):
        department = parent_view.department
        options = [discord.SelectOption(label=team) for team in departments[department].keys()]
        super().__init__(placeholder="Choose your Department.", options=options)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.team = self.values[0]
        await interaction.response.send_message(
            f"Division **{self.parent_view.team}** selected. Now choose a Division.",
            ephemeral=True,
            view=JobView(self.parent_view)
        )

# View for selecting a job and submitting the request
class JobView(View):
    def __init__(self, parent_view):
        super().__init__(timeout=300)
        self.parent_view = parent_view
        self.add_item(JobSelect(parent_view))
        self.add_item(SubmitButton(parent_view))

# Dropdown
class JobSelect(Select):
    def __init__(self, parent_view):
        department = parent_view.department
        team = parent_view.team
        options = [discord.SelectOption(label=job) for job in departments[department][team]["1"]]
        super().__init__(placeholder="Choose your Division.", options=options)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.job = self.values[0]
        await interaction.response.defer(ephemeral=True)

# Button for submitting the role request
class SubmitButton(Button):
    def __init__(self, parent_view):
        super().__init__(label="Submit", style=discord.ButtonStyle.success)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)

        member = self.parent_view.member
        department = self.parent_view.department
        team = self.parent_view.team
        job = self.parent_view.job

        if not department or not job:
            await interaction.response.send_message(
                "❗ Please complete all selections before submitting.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="New Role Request",
            description=(
                f"**User:** {member.mention}\n"
                f"**Sector:** {department}\n"
                f"**Department:** {team}\n"
                f"**Division:** {job}"
            ),
            color=discord.Color.blue(),
        )

        channel: discord.TextChannel = interaction.guild.get_channel(int(os.getenv("APPROVAL_CHANNEL_ID")))
        await channel.send(embed=embed, view=ApprovalView(member, department, team, job))

        # Log the submission
        log_channel = interaction.guild.get_channel(int(os.getenv("LOG_CHANNEL_ID")))
        if log_channel:
            await log_channel.send(f"📥 {member.mention} applied for {department} - {job}")

            # Send info to bot logs
            logging.log(logging.INFO, f"{member.mention} applied for {department} - {job}")

        await interaction.followup.send(content="Your request has been submitted for approval!")

async def setup(bot):
    await bot.add_cog(Induction(bot))
