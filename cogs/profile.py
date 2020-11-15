import os
import psycopg2
import discord
from discord.ext import commands


class ProfileCog(commands.Cog, name='profile'):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='profile', pass_context=True)
    async def profile(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Default command')

    @profile.command(name="create", pass_context=True)
    async def create(self, ctx):

        conn = None
        await ctx.send('PROFILE CREATE: starting command...')

        try:
            conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
            cur = conn.cursor()
            await ctx.send('PROFILE CREATE: successfully connected to database...')

            author = str(ctx.message.author)
            author_id = ctx.message.author.id
            cur.execute(f"SELECT * FROM profiles WHERE user_id={author_id}")
            await ctx.send('PROFILE CREATE: successfully executed first query...')
            await ctx.send(f'PROFILE CREATE: {cur.rowcount} records found.')

            if cur.rowcount == 0:
                await ctx.send('PROFILE CREATE: no profile found. creating profile...')

                cur.execute("INSERT INTO profiles VALUES (%s, %s)", (author_id, None))
                await ctx.send(f'PROFILE CREATE: successfully executed second query. new profile created for {author}.')

                conn.commit()
                await ctx.send('PROFILE CREATE: database changes successfully committed.')
            else:
                await ctx.send('PROFILE CREATE: profile already exists.')

        except (Exception, psycopg2.DatabaseError) as error:
            await ctx.send(error)
        finally:
            if conn is not None:
                conn.close()
                await ctx.send('PROFILE CREATE: successfully closed connection to database...')

    @profile.command(name="delete", pass_context=True)
    async def delete(self, ctx, *args: discord.User):

        if len(args) == 0 or args[0] == ctx.message.author:
            user_id_to_delete = ctx.message.author.id
            username = str(ctx.message.author)
        elif len(args) == 1:
            if ctx.message.author.guild_permissions.kick_members:
                user_id_to_delete = args[0].id
                username = str(args[0])
            else:
                await ctx.send(':no_entry:⠀⠀**Error!!**⠀you need the kick members permission to delete another user\'s profile')
                raise NameError('MissedPermissions')
        else:
            await ctx.send(':no_entry:⠀⠀**Error!!**⠀you can only delete one profile at a time')
            raise NameError('TooManyArgs')

        conn = None
        await ctx.send('PROFILE DELETE: starting command...')

        try:
            conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
            cur = conn.cursor()
            await ctx.send('PROFILE DELETE: successfully connected to database...')

            cur.execute(f"SELECT * FROM profiles WHERE user_id={user_id_to_delete}")
            await ctx.send('DELETE CREATE: successfully executed first query...')
            await ctx.send(f'DELETE CREATE: {cur.rowcount} records found.')

            if cur.rowcount == 1:
                await ctx.send('DELETE CREATE: profile found. deleting profile...')

                cur.execute(f"DELETE FROM profiles WHERE user_id={user_id_to_delete}")
                await ctx.send(f'PROFILE DELETE: successfully executed second query. profile for {username} deleted.')

                conn.commit()
                await ctx.send('PROFILE DELETE: database changes successfully committed.')
            else:
                await ctx.send(f'PROFILE DELETE: no profile exists for {username}.')

        except (Exception, psycopg2.DatabaseError) as error:
            await ctx.send(error)
        finally:
            if conn is not None:
                conn.close()
                await ctx.send('PROFILE DELETE: successfully closed connection to database...')

    @profile.command(name="update", pass_context=True)
    async def update(self, ctx, property, *args):
        author_id = ctx.message.author.id

        if property == "psn":
            conn = None
            await ctx.send('PROFILE UPDATE: starting command...')

            try:
                conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
                cur = conn.cursor()
                await ctx.send('PROFILE UPDATE: successfully connected to database...')

                sql = """UPDATE profiles SET psn = %s WHERE user_id = %s"""
                if len(args) == 0:
                    cur.execute(sql, (None, author_id))
                else:
                    cur.execute(sql, (args[0], author_id))
                await ctx.send('DELETE UPDATE: successfully executed query...')

                conn.commit()
                await ctx.send('PROFILE UPDATE: database changes successfully committed.')
            except (Exception, psycopg2.DatabaseError) as error:
                await ctx.send(error)
            finally:
                if conn is not None:
                    conn.close()
                    await ctx.send('PROFILE UPDATE: successfully closed connection to database...')


def setup(bot):
    bot.add_cog(ProfileCog(bot))
