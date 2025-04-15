import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput, Select
import os
from dotenv import load_dotenv
import random

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GUILD_ID = int(os.getenv("SERVER_ID"))
APPROVAL_CHANNEL_ID = int(os.getenv("APPROVAL_CHANNEL_ID"))
ONBOARDING_EXCLUSION_ROLE = int(os.getenv("ONBOARDING_EXCLUSION_ROLE_ID"))
APPROVER_ROLE_ID = int(os.getenv("APPROVER_ROLE_ID"))
log_channel_id = int(os.getenv("LOG_CHANNEL_ID"))

# Set up bot intents for member and message content access
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Initialize the bot with a command prefix and intents
bot = commands.Bot(command_prefix="/", intents=intents, case_insensitive=True)


# Command to start the onboarding process
@bot.tree.command(
    name="traxus",
    description="Start the onboarding process",
    guild=discord.Object(id=GUILD_ID),
)
async def traxus(interaction: discord.Interaction):
    # Check if the user has the exclusion role (already onboarded)
    if any(role.id == ONBOARDING_EXCLUSION_ROLE for role in interaction.user.roles):
        await interaction.response.send_message(
            "# Already onboarded.", ephemeral=True  # Message visible only to the user
        )
        return

    # Display the onboarding view to the user
    view = OnboardingView(interaction.user)
    await interaction.response.send_message(
        "# Welcome, Valued Asset, to TRAXUS Industries. Please select your desired department below",
        view=view,
        ephemeral=True,
    )


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


# Event triggered when the bot is ready
@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    try:
        # Sync application commands with the guild
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced commands: {[cmd.name for cmd in synced]}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    # Notify the designated channel that the bot is online
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("# TRAXUS TRAX-S SYSTEM IS NOW ONLINE")


# Dictionary defining departments and their respective jobs
departments = {
    "Asset": ["Asset"],
    "Security": [
        "Security Staff",
        "Exfiltration Heavy Weapons",
        "Exfiltration Demolition",
        "Exfiltration",
    ],
    "Finance & Logistics": ["Logistics ", "Logistics Maintenance", "Logistics Cargo"],
    "Technical": ["Engineer", "Designer", "Skunkworks "],
    "Marketing": ["Communication ", "Communication: propaganda"],
    "Intelligence": ["IT", "Hygiene", "Culinary"],
    "Staff": ["HR"],
}


# Function to log actions to the log channel
async def log_position(message: str):
    channel = bot.get_channel(log_channel_id)
    if channel:
        await channel.send(message)


# View for approving or rejecting role requests
class ApprovalView(View):
    def __init__(self, member, department, job):
        super().__init__(timeout=None)
        self.member = member
        self.department = department
        self.job = job
        self.add_item(ApproveButton(self))
        self.add_item(RejectButton(self))


# Button for approving a role request
class ApproveButton(Button):
    def __init__(self, parent):
        super().__init__(label="Approve ✅", style=discord.ButtonStyle.success)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        # Check if the user has the approver role
        if not any(role.id == APPROVER_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message(
                "You are not authorized...", ephemeral=True
            )
            return

        # Notify the member about the approval
        try:
            await self.parent.member.send(
                f"✅ Your role as **{self.parent.job}** in **{self.parent.department}** has been approved!"
            )
        except discord.Forbidden:
            pass

        # Update the member's nickname
        full_nick = f"{self.parent.member.display_name} | TRAXUS {self.parent.job}"
        short_nick = f"TRAXUS {self.parent.job}"
        final_nick = full_nick if len(full_nick) <= 32 else short_nick

        try:
            await self.parent.member.edit(nick=final_nick)
        except discord.Forbidden:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "⚠️ I don't have permission to change the user's nickname.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "⚠️ I don't have permission to change the user's nickname.",
                    ephemeral=True,
                )
        except Exception as e:
            await interaction.followup.send(
                f" Failed to change nickname: {e}", ephemeral=True
            )

        # Log the approval action
        await log_position(
            f"✅ Application approved by {interaction.user.mention} for {self.parent.member.mention}"
        )

        # Update the message and notify the approver
        await interaction.message.edit(view=None)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "✅ Application approved.", ephemeral=True
            )
        else:
            await interaction.followup.send("✅ Application approved.", ephemeral=True)


# Button for rejecting a role request
class RejectButton(Button):
    def __init__(self, parent):
        super().__init__(label="Reject ❌", style=discord.ButtonStyle.danger)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        # Check if the user has the approver role
        if not any(role.id == APPROVER_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message(
                "You are not authorized...", ephemeral=True
            )
            return

        # Display a modal to collect the rejection reason
        await interaction.response.send_modal(
            RejectReasonModal(self.parent, interaction.user)
        )


# Modal for entering the rejection reason
class RejectReasonModal(Modal, title="Rejection Reason"):
    def __init__(self, parent, approver):
        super().__init__()
        self.parent = parent
        self.approver = approver
        self.reason = TextInput(
            label="Reason", style=discord.TextStyle.paragraph, required=True
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        # Notify the member about the rejection
        try:
            await self.parent.member.send(
                f"❌ Your application for **{self.parent.job}** in **{self.parent.department}** "
                f"has been rejected.\n**Reason:** {self.reason.value}"
            )
        except discord.Forbidden:
            pass

        # Log the rejection action
        await log_position(
            f"❌ Application rejected by {self.approver.mention} for {self.parent.member.mention} — Reason: {self.reason.value}"
        )

        # Update the message and notify the approver
        await interaction.message.edit(view=None)
        await interaction.response.send_message(
            "❌ Application rejected.", ephemeral=True
        )


# View for the onboarding process
class OnboardingView(View):
    def __init__(self, member):
        super().__init__(timeout=300)  # Timeout after 5 minutes
        self.member = member
        self.department = None
        self.job = None
        self.add_item(DepartmentSelect(self))


# Dropdown for selecting a department
class DepartmentSelect(Select):
    def __init__(self, parent_view):
        options = [discord.SelectOption(label=dept) for dept in departments.keys()]
        super().__init__(placeholder="Choose your department.", options=options)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        # Save the selected department and display the job selection view
        self.parent_view.department = self.values[0]
        await interaction.response.send_message(
            f"# **{self.parent_view.department}** Department selected. Now pick a job.",
            ephemeral=True,
            view=JobView(self.parent_view),
        )


# View for selecting a job and submitting the request
class JobView(View):
    def __init__(self, parent_view):
        super().__init__(timeout=300)  # Timeout after 5 minutes
        self.parent_view = parent_view
        self.add_item(JobSelect(parent_view))
        self.add_item(SubmitButton(parent_view))


# Dropdown for selecting a job
class JobSelect(Select):
    def __init__(self, parent_view):
        options = [
            discord.SelectOption(label=job)
            for job in departments[parent_view.department]
        ]
        super().__init__(placeholder="Choose your job.", options=options)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        # Save the selected job
        self.parent_view.job = self.values[0]
        await interaction.response.defer(ephemeral=True)


# Button for submitting the role request
class SubmitButton(Button):
    def __init__(self, parent_view):
        super().__init__(label="Submit", style=discord.ButtonStyle.success)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        member = self.parent_view.member
        department = self.parent_view.department
        job = self.parent_view.job

        # Ensure all selections are made before submission
        if not department or not job:
            await interaction.response.send_message(
                "❗ Please complete all selections before submitting.", ephemeral=True
            )
            return

        # Create an embed for the role request and send it to the approval channel
        channel = bot.get_channel(APPROVAL_CHANNEL_ID)
        embed = discord.Embed(
            title="New Role Request",
            description=f"**User:** {member.mention}\n**Department:** {department}\n**Job:** {job}",
            color=discord.Color.blue(),
        )
        await channel.send(embed=embed, view=ApprovalView(member, department, job))

        # Notify the user about the submission
        await interaction.response.send_message(
            "Your request has been submitted for approval!", ephemeral=True
        )

        # Log the submission
        await log_position(f"📥 {member.mention} applied for {department} - {job}")


# Run the bot
bot.run(TOKEN)
