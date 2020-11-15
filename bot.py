import os
import psycopg2
import discord
import logging
from discord.ext import commands
from database.database import Postgres


def get_prefix(bot, message):
    """a callable prefix for our bot which can be customized by each guild"""

    # set default prefix
    default_prefix = ';'

    # check if we're outside a guild (like in a DM, etc.)
    if not message.guild:
        # only allow the default prefix or mention to be used in DMs
        return commands.when_mentioned_or(*default_prefix)(bot, message)

    with Postgres() as db:
        # check if this guild has a custom prefix
        prefix = db.query('SELECT prefix FROM prefixes WHERE guild_id = %s', (message.guild.id,))

        # if so, return that prefix
        if prefix:
            return commands.when_mentioned_or(str(*prefix[0]))(bot, message)

    # otherwise return the default prefix
    return commands.when_mentioned_or(*default_prefix)(bot, message)


# Below cogs represents our folder our cogs are in. Following is the file name. So 'meme.py' in cogs, would be cogs.meme
# Think of it like a dot path import
initial_cogs = ['cogs.starboard', 'cogs.owner', 'cogs.wishwall']

bot = commands.Bot(command_prefix=get_prefix, description='A bot for GoldxGuns')


@bot.command(name='ping')
async def ping(ctx):
    """returns the bot's latency in milliseconds"""

    # return ping
    await ctx.send(f':ping_pong:⠀⠀**Pong!**⠀{round(bot.latency, 3)}ms')


@bot.group(name='prefix', pass_context=True)
async def prefix(ctx):
    """returns the bot's prefix for this guild"""

    # check that we're not in a subcommand
    if ctx.invoked_subcommand is None:
        # return prefix
        await ctx.send(f'My prefix is `{get_prefix(bot, ctx.message)[2]}`')


@prefix.command(name='set', no_pm=True, hidden=True, pass_context=True, aliases=['change'])
@commands.has_guild_permissions(administrator=True)
async def set(ctx, new_prefix):
    """changes the bot's prefix for this guild"""

    # instantiate database
    with Postgres() as db:
        # check if there's already an entry for this guild
        entry_exists = db.query('SELECT prefix FROM prefixes WHERE guild_id = %s', (ctx.guild.id,))

        # if there is, then update the entry
        if entry_exists:
            db.execute('UPDATE prefixes SET prefix=%s WHERE guild_id = %s', (new_prefix, ctx.guild.id))
        # else create a new entry for this guild
        else:
            db.execute('INSERT INTO prefixes VALUES (%s, %s)', (ctx.guild.id, new_prefix))

        # check to see if we successfully wrote to the database by checking if a row was modified
        if db.cursor.rowcount == 1:
            await ctx.send(f':white_check_mark:⠀⠀**Success!**⠀my prefix is now `{new_prefix}`')
        # else something went wrong
        else:
            await ctx.send('<:wrong:742105251271802910>⠀⠀**Error!!**⠀my prefix couldn\'t be changed because something went wrong')


@bot.command(name='server')
async def server(ctx):
    await ctx.send("This command isn't ready yet!")


@bot.command(name='credits')
async def credits(ctx):
    embed = discord.Embed(title='Development Credits', description='Thank you to all of the following folks for making Gigi possible.', colour=0xffff33)
    embed.set_thumbnail(url=bot.user.avatar_url)
    embed.add_field(name='Lead Developer', value='@ShiinaBat#8227', inline=True)
    embed.add_field(name='Developers', value='@Adam.M#9788\n@Element#1337', inline=True)
    embed.add_field(name='Alpha Testers', value='@AzureEiyu#9781, @CursedQuill#5719, @Isaac2K#1948, @Kurokaito#5489, @Vyxea#0001', inline=False)
    embed.add_field(name='Character Designer', value='NEBULArobo ([https://nebularobo.carrd.co/](https://nebularobo.carrd.co/))', inline=False)
    embed.add_field(name='Icon Artist', value='crankiereddy ([https://twitter.com/crankiereddy](https://twitter.com/crankiereddy))', inline=False)
    await ctx.send(content=None, embed=embed)


# Here we load our extensions(cogs) listed above in [initial_extensions].
if __name__ == '__main__':
    for extension in initial_cogs:
        bot.load_extension(extension)

    with Postgres() as db:
        db.create_tables()


@bot.event
async def on_ready():
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')

    # Changes our bots Playing Status. type=1(streaming) for a standard game you could remove type and url.
    print(f'Successfully logged in and booted...!')


bot.run(os.environ.get("TOKEN"), bot=True, reconnect=True)
