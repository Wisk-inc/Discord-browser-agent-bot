import os
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import json
from datetime import datetime
from pathlib import Path
import io

from browser_use import Agent, Controller, Browser
from browser_use.browser.browser import BrowserConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_deepseek import ChatDeepSeek

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CONFIG_FILE = 'user_configs.json'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

user_configs = {}

def load_configs():
    global user_configs
    if Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE, 'r') as f:
            user_configs = json.load(f)

def save_configs():
    with open(CONFIG_FILE, 'w') as f:
        json.dump(user_configs, f, indent=2)

load_configs()

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f'Logged in as {bot.user} (ID: {bot.user.id})')
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error syncing commands: {e}')

@bot.tree.command(name="api", description="Set your API provider and key")
@app_commands.describe(
    provider="Choose your LLM provider",
    api_key="Your API key for the selected provider"
)
@app_commands.choices(provider=[
    app_commands.Choice(name="Google Gemini", value="google"),
    app_commands.Choice(name="OpenAI", value="openai"),
    app_commands.Choice(name="Anthropic", value="anthropic"),
    app_commands.Choice(name="DeepSeek", value="deepseek"),
])
async def api_command(interaction: discord.Interaction, provider: str, api_key: str):
    user_id = str(interaction.user.id)
    
    if user_id not in user_configs:
        user_configs[user_id] = {}
    
    user_configs[user_id]['provider'] = provider
    user_configs[user_id]['api_key'] = api_key
    
    save_configs()
    
    provider_names = {
        'google': 'Google Gemini',
        'openai': 'OpenAI',
        'anthropic': 'Anthropic',
        'deepseek': 'DeepSeek'
    }
    
    embed = discord.Embed(
        title="✅ API Configuration Set",
        description=f"Your API provider has been configured successfully!",
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Provider", value=provider_names.get(provider, provider), inline=True)
    embed.add_field(name="Status", value="✓ API Key Saved", inline=True)
    embed.set_footer(text=f"User: {interaction.user.name}")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="browse", description="Browse a URL and complete a task")
@app_commands.describe(
    url="The URL to browse",
    task="The task for the AI agent to complete"
)
async def browse_command(interaction: discord.Interaction, url: str, task: str):
    user_id = str(interaction.user.id)
    
    if user_id not in user_configs or 'provider' not in user_configs[user_id]:
        embed = discord.Embed(
            title="❌ API Not Configured",
            description="Please set up your API provider first using `/api`",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await interaction.response.defer()
    
    config = user_configs[user_id]
    provider = config['provider']
    api_key = config['api_key']
    
    try:
        if provider == 'google':
            llm = ChatGoogleGenerativeAI(
                model='gemini-2.0-flash-exp',
                google_api_key=api_key,
                temperature=0.0
            )
        elif provider == 'openai':
            llm = ChatOpenAI(
                model='gpt-4o',
                api_key=api_key,
                temperature=0.0
            )
        elif provider == 'anthropic':
            llm = ChatAnthropic(
                model='claude-3-5-sonnet-20241022',
                api_key=api_key,
                temperature=0.0
            )
        elif provider == 'deepseek':
            llm = ChatDeepSeek(
                model='deepseek-chat',
                api_key=api_key,
                temperature=0.0
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        full_task = f"Go to {url} and {task}"
        
        controller = Controller()
        browser_config = BrowserConfig(
            headless=True,
            disable_security=True,
        )
        browser = Browser(config=browser_config)
        
        agent = Agent(
            task=full_task,
            llm=llm,
            controller=controller,
            browser=browser,
        )
        
        initial_embed = discord.Embed(
            title="🤖 Browser Agent Working",
            description=f"**Task:** {task}\n**URL:** {url}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        initial_embed.add_field(name="Status", value="🔄 Processing...", inline=False)
        initial_embed.set_footer(text=f"Requested by {interaction.user.name}")
        
        message = await interaction.followup.send(embed=initial_embed)
        
        screenshots = []
        import base64
        
        async def on_step_end(agent_instance):
            # Get the latest history entry
            if agent_instance.state.history and len(agent_instance.state.history.history) > 0:
                latest_history = agent_instance.state.history.history[-1]
                if hasattr(latest_history, 'state') and hasattr(latest_history.state, 'screenshot'):
                    screenshot = latest_history.state.screenshot
                    if screenshot:
                        step_num = len(screenshots) + 1
                        screenshots.append(screenshot)
                        
                        screenshot_bytes = base64.b64decode(screenshot)
                        file = discord.File(io.BytesIO(screenshot_bytes), filename=f'screenshot_{step_num}.png')
                        
                        step_embed = discord.Embed(
                            title=f"📸 Step {step_num}",
                            description=f"**Task:** {task}",
                            color=discord.Color.purple(),
                            timestamp=datetime.utcnow()
                        )
                        step_embed.set_image(url=f"attachment://screenshot_{step_num}.png")
                        step_embed.set_footer(text=f"Browser Agent | {interaction.user.name}")
                        
                        await interaction.followup.send(embed=step_embed, file=file)
        
        result = await agent.run(on_step_end=on_step_end)
        
        final_embed = discord.Embed(
            title="✅ Task Completed",
            description=f"**Task:** {task}\n**URL:** {url}",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        final_embed.add_field(name="Steps Taken", value=str(len(screenshots)), inline=True)
        final_embed.add_field(name="Screenshots", value=str(len(screenshots)), inline=True)
        final_embed.set_footer(text=f"Completed for {interaction.user.name}")
        
        await message.edit(embed=final_embed)
        
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Error",
            description=f"An error occurred while processing your request",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        error_embed.add_field(name="Error Details", value=f"```{str(e)[:1000]}```", inline=False)
        error_embed.set_footer(text=f"User: {interaction.user.name}")
        
        await interaction.followup.send(embed=error_embed)

@bot.tree.command(name="status", description="Check your API configuration status")
async def status_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    if user_id not in user_configs or 'provider' not in user_configs[user_id]:
        embed = discord.Embed(
            title="ℹ️ API Status",
            description="No API configuration found",
            color=discord.Color.orange()
        )
        embed.add_field(name="Next Step", value="Use `/api` to configure your provider", inline=False)
    else:
        config = user_configs[user_id]
        provider_names = {
            'google': 'Google Gemini',
            'openai': 'OpenAI',
            'anthropic': 'Anthropic',
            'deepseek': 'DeepSeek'
        }
        
        embed = discord.Embed(
            title="✅ API Status",
            description="Your API is configured and ready",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Provider", value=provider_names.get(config['provider'], config['provider']), inline=True)
        embed.add_field(name="Status", value="✓ Active", inline=True)
    
    embed.set_footer(text=f"User: {interaction.user.name}")
    await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == '__main__':
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set")
        exit(1)
    
    bot.run(DISCORD_TOKEN)
