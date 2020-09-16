# guardian.py

import os, random, time, json

import requests, json, html
from datetime import datetime, timedelta

import discord
from discord.ext import commands


bot = commands.Bot(command_prefix=";")

# Initialisation des dossiers et fichiers au démarrage du Bot - seulement s'ils n'existent pas
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"Test CELCAT"))
    # Importation du module
    try:
        bot.load_extension("EDT")
    except Exception as e:
        print('{}: {}'.format(type(e).__name__, e))

    print(f'Logged in as {bot.user.name} on {len(bot.guilds)} servers')

#### Load - Unload - Reload an extension
@bot.command(name='reload')
@commands.is_owner()
async def reload(ctx, module : str):
    """Reloads a module."""

    try:
        bot.unload_extension(module)
        bot.load_extension(module)
    except Exception as e:
        await ctx.send('{}: {}'.format(type(e).__name__, e))
    else:
        await ctx.send('`Module {} has been successfully reloaded.`'.format(module))

@bot.command(name='load')
@commands.is_owner()
async def load(ctx, module : str):
    """Loads a module."""

    try:
        bot.load_extension(module)
    except Exception as e:
        await ctx.send('{}: {}'.format(type(e).__name__, e))
    else:
        await ctx.send('`Module {} has been loaded.`'.format(module))

@bot.command(name='unload')
@commands.is_owner()
async def unload(ctx, module : str):
    """Unloads a module."""

    try:
        bot.unload_extension(module)
    except Exception as e:
        await ctx.send('{}: {}'.format(type(e).__name__, e))
    else:
        await ctx.send('`Module {} has been unloaded.`'.format(module))


###### ON ERROR ######
@bot.event
async def on_command_error(ctx, error):
    print(f"ERR - {ctx.command} - {error}")


with open("AdabGuardian/tok.json", 'r') as readFile:
    TOKEN = json.load(readFile)
bot.run(TOKEN)
