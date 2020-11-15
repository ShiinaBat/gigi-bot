import discord
import logging
from discord.ext import commands
from database.database import Postgres

STAR_URL = 'https://cdn.discordapp.com/attachments/767568459939708950/777605519623585822/11_Discord_icon_4_20.png'
STAR_PIN_URL = 'https://cdn.discordapp.com/attachments/767568459939708950/777605535801016350/11_Discord_icon_4_80.png'
ERROR_URL = 'https://cdn.discordapp.com/attachments/767568459939708950/777606962480807956/11_Discord_icon_2_80.png'
SUCCESS_URL = 'https://cdn.discordapp.com/attachments/767568459939708950/767568508414066739/Status_Indicators12.png'


class StarboardCog(commands.Cog, name='starboard'):

    def __init__(self, bot):
        self.bot = bot

    def get_starboard(self, guild_id):
        with Postgres() as db:
            starboard_from_db = db.query('SELECT * FROM starboard WHERE guild_id = %s', (guild_id,))

        if starboard_from_db:
            starboard_settings = {
                "channel": self.bot.get_channel((starboard_from_db[0])[1]),
                "star_emoji": (starboard_from_db[0])[2],
                "count": (starboard_from_db[0])[3],
                "conf_emoji": (starboard_from_db[0])[4]
            }
            return starboard_settings

        else:
            return None

    def get_error_embed(self, ctx, error_code):

        if error_code == "StarboardNotExist":
            error_message = "this guild doesn't seem to have a starboard"
            footer_message = f"create one with '{ctx.prefix}starboard create'"

        elif error_code == "StarboardAlreadyExists":
            error_message = "this guild already has a starboard"
            footer_message = f"update its settings with '{ctx.prefix}starboard update'"

        embed = discord.Embed(title='Uh oh, something went wrong!',
                              description=error_message,
                              colour=0xd32b1d)
        embed.set_thumbnail(url=ERROR_URL)

        embed.set_footer(icon_url='', text=footer_message)

        return embed

    def get_success_embed(self, ctx, success_code):

        if success_code == "StarboardCreated":
            success_message = "starboard created successfully"
        elif success_code == "StarboardDeleted":
            success_message = "starboard deleted successfully"

        embed = discord.Embed(title='Yeehaw, the command worked!',
                              description=success_message,
                              colour=0x56b218)
        embed.set_thumbnail(url=SUCCESS_URL)

        return embed

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, ctx):
        """post starred messages to the starboard"""

        # grab the starboard's settings from the database
        starboard_settings = self.get_starboard(ctx.guild_id)

        # store the details of the invoking message for easy access
        channel = self.bot.get_channel(ctx.channel_id)
        message = await channel.fetch_message(ctx.message_id)

        # store the details of the invoking reaction for easy access
        reaction = discord.utils.get(message.reactions, emoji=ctx.emoji.name)
        already_posted = discord.utils.get(message.reactions, emoji=starboard_settings["conf_emoji"])

        # check if the emoji is correct, that it meets or exceeds the required count, that this message hasn't been
        # posted to the starboard already, and that this message isn't in the starboard channel
        if ctx.emoji.name == starboard_settings["star_emoji"] and reaction.count >= starboard_settings["count"] and (
                not already_posted or not already_posted.me) and ctx.channel_id != starboard_settings["channel"].id:

            copy_embed = ""

            # check if the starred message is an embed
            if message.embeds:
                # if so, copy it into a dict so we can work with it
                copy_embed = message.embeds[0].to_dict()

                # let's start with the embed's description
                if message.content:
                    # if the message has both content and an embed, then we'll need to copy both
                    content = message.content.__add__(f'\n\n**Link Preview:**\n{copy_embed["description"]}')
                else:
                    # otherwise we'll just copy the description
                    content = copy_embed["description"]

                # then append any fields it has on the bottom, not elegant for inlines but deal
                if "fields" in copy_embed:
                    for embeds in message.embeds:
                        for field in embeds.fields:
                            content = content.__add__(f'\n\n**{field.name}**')
                            content = content.__add__(f'\n{field.value}')
            else:
                # if not, we'll just use the message's content
                content = message.content

            # create the embed to send to the starboard
            embed = discord.Embed(title=f"{message.author} said...",
                                  description=f'{content}\n\n[Jump to Message](https://discordapp.com/channels/{ctx.guild_id}/{ctx.channel_id}/{ctx.message_id})',
                                  colour=0x784fd7,
                                  timestamp=message.created_at)

            # add the author's avatar as the thumbnail
            embed.set_thumbnail(url=message.author.avatar_url)

            # add attached image or link preview if there is one
            if message.embeds:
                if "image" in copy_embed:
                    embed.set_image(url=copy_embed["image"]["url"])
                elif "video" in copy_embed:
                    embed.set_image(url=copy_embed["thumbnail"]["url"])
            elif message.attachments:
                embed.set_image(url=message.attachments[0].url)

            # add a pretty footer
            embed.set_footer(icon_url=STAR_URL, text='Original Posted')

            # send the embed to the starboard
            await starboard_settings["channel"].send(content=f"> **Posted in** {channel.mention} by {message.author.mention}", embed=embed)

            # add a reaction to confirm that the message was posted to the starboard
            await message.add_reaction(starboard_settings["conf_emoji"])

    @commands.group(name='starboard', hidden=True, pass_context=True, aliases=['sb', 'sboard', 'star'])
    async def starboard(self, ctx):
        pass

    @starboard.command(name="create", hidden=True, pass_context=True, aliases=['new', 'make', 'bind'])
    @commands.has_guild_permissions(administrator=True)
    async def create(self, ctx, channel: discord.TextChannel):
        """creates a starboard for this guild"""

        if not self.get_starboard(ctx.guild.id):
            with Postgres() as db:
                db.execute("INSERT INTO starboard VALUES (%s, %s, DEFAULT, DEFAULT, DEFAULT)", (ctx.guild.id, channel.id))

                if db.cursor.rowcount == 1:
                    await ctx.send(content=None, embed=self.get_success_embed(ctx, "StarboardCreated"))
                else:
                    await ctx.send("something went wrong, starboard could not be created")
        else:
            await ctx.send(content=None, embed=self.get_error_embed(ctx, "StarboardAlreadyExists"))

    @starboard.command(name="settings", hidden=False, pass_context=True, aliases=['information', 'info'])
    async def settings(self, ctx):
        """returns the starboard's current settings"""

        # grab the starboard's settings from the database
        starboard_settings = self.get_starboard(ctx.guild.id)

        if starboard_settings:
            # compile the starboard settings into an embed and send it to the channel this command was invoked in
            embed = discord.Embed(colour=0x784fd7)

            embed.set_thumbnail(url=STAR_PIN_URL)

            embed.add_field(name='Channel', value=f'{starboard_settings["channel"].mention}', inline=False)
            embed.add_field(name='Threshold', value=f'**{starboard_settings["count"]}** reaction(s)', inline=False)
            embed.add_field(name='Star Emoji', value=f'{starboard_settings["star_emoji"]} ⠀', inline=False)
            embed.add_field(name='Confirm Emoji', value=f'{starboard_settings["conf_emoji"]}⠀', inline=False)

            embed.set_footer(text=f'change settings with {ctx.prefix}starboard update')

            await ctx.send(content=f"> **Starboard Settings** for **{ctx.guild.name}**", embed=embed)

        else:
            await ctx.send(content=None, embed=self.get_error_embed(ctx, "StarboardNotExist"))

    @starboard.command(name="update", hidden=True, pass_context=True, aliases=['set', 'change', 'modify'])
    @commands.has_guild_permissions(administrator=True)
    async def update(self, ctx):
        """changes a setting on the starboard"""

        foo = bar

    @starboard.command(name="delete", hidden=True, pass_context=True, aliases=['del', 'remove', 'yeet'])
    @commands.has_guild_permissions(administrator=True)
    async def delete(self, ctx):
        """deletes the starboard for this guild"""

        if self.get_starboard(ctx.guild.id):
            with Postgres() as db:
                db.execute('DELETE FROM starboard WHERE guild_id = %s', (ctx.guild.id,))

                if db.cursor.rowcount == 1:
                    await ctx.send(content=None, embed=self.get_success_embed(ctx, "StarboardDeleted"))
                else:
                    await ctx.send("something went wrong, starboard could not be deleted")

        else:
            await ctx.send(content=None, embed=self.get_error_embed(ctx, "StarboardNotExist"))


def setup(bot):
    bot.add_cog(StarboardCog(bot))
