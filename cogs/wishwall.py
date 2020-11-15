import time
import discord
from discord.ext import commands


class WishCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='wish')
    async def wish(self, ctx, *args):
        wish = ' '.join(args)

        if ctx.channel.id == 746220388866064474:
            platform = 'PS4'
        if ctx.channel.id == 746576322452783175:
            platform = 'PC'
        else:
            return
        if len(wish) == 0:
            empty_wish_embed = discord.Embed(title="Riven demands you submit a wish properly",
                                             description="Please include what your wish is with your command. i.e. "
                                                         "?wish Izanagi's Catalyst")
            empty_wish_embed.set_thumbnail(
                url="https://media.discordapp.net/attachments/742534075583037540/746924606753079346/51dhk8om09q11.jpg")
            await ctx.channel.send(embed=empty_wish_embed)
            return

        wish = ' '.join(args)
        wish_embed = discord.Embed(title="{} has made a wish!".format(ctx.message.author),
                                   description='{}'.format(wish), color=0xff0209)
        wish_embed.set_thumbnail(
            url="https://media.discordapp.net/attachments/742534075583037540/746924606753079346/51dhk8om09q11.jpg")
        wish_embed.add_field(name="Platform:", value="{}".format(platform), inline=True)
        wish_embed.add_field(name="Created by:", value="{}".format(ctx.message.author.mention), inline=True)
        wish_embed.set_footer(text="Riven hears your call.")
        await ctx.channel.send(embed=wish_embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        user = await self.bot.fetch_user(message.author.id)
        if (message.channel.id == 746220388866064474 or
            message.channel.id == 746576322452783175) and not user.bot:
            await discord.Message.delete(message)
        if (message.channel.id == 746220388866064474 or
            message.channel.id == 746576322452783175) and user.bot:
            emoji = '\U0000274c'
            await discord.Message.add_reaction(message, emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        user = await self.bot.fetch_user(payload.user_id)
        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        embed = None
        if 746220388866064474 == message.channel.id or 746576322452783175 == message.channel.id:
            reaction = payload.emoji
            if message.embeds:
                embed = message.embeds[0].title

            if str(reaction) == '❌' and not user.bot:
                await discord.Message.delete(message)
            elif user.bot and str(embed) == 'Riven demands you submit a wish properly':
                await asyncio.sleep(5)
                await discord.Message.delete(message)


def setup(bot):
    bot.add_cog(WishCog(bot))
