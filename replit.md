# Browser Use Discord Bot

## Overview
This project has been converted from a browser automation web UI to a Discord bot. The bot allows users to control browser automation through Discord slash commands.

## Recent Changes (September 30, 2025)
- Installed Python 3.11 and all required dependencies
- Installed discord.py for Discord bot functionality
- Installed playwright with Chromium browser for web automation
- Created Discord bot with slash commands: `/api`, `/browse`, and `/status`
- Configured workflow to run the Discord bot automatically

## Project Architecture

### Core Components
- **discord_bot.py**: Main Discord bot implementation with slash commands
- **browser-use library**: Browser automation framework
- **LangChain integrations**: Support for multiple LLM providers (Google Gemini, OpenAI, Anthropic, DeepSeek)
- **Playwright**: Headless browser automation

### Discord Commands
1. `/api <provider> <api_key>` - Configure your LLM provider
   - Providers: Google Gemini, OpenAI, Anthropic, DeepSeek
   - Stores API key securely per user
   - Shows confirmation embed when set

2. `/browse <url> <task>` - Automate browser tasks
   - Takes a URL and task description
   - Uses configured LLM to control browser
   - Sends screenshot embeds for each step
   - Shows final completion status

3. `/status` - Check your API configuration
   - Shows current provider and status
   - Ephemeral message (only visible to you)

### User Configuration
- User configs stored in `user_configs.json`
- Each user can have their own API provider and key
- Configurations persist across bot restarts

## Environment Setup
- Python 3.11 with all dependencies from requirements.txt
- Discord.py for bot functionality
- Playwright Chromium browser installed
- Environment variables managed through .env file
- Discord token stored in start_bot.sh

## Workflow
- **Discord Bot**: Runs `bash start_bot.sh`
- Console output type for monitoring
- Auto-starts on Replit environment

## Usage Flow
1. User runs `/api google <gemini-api-key>` to configure provider
2. Bot confirms API is set with embed message
3. User runs `/browse https://example.com search for products`
4. Bot starts browser automation and sends screenshot embeds for each step
5. Bot sends completion embed when done
