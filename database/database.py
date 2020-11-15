import os
import psycopg2


# Combination of https://softwareengineering.stackexchange.com/a/362352 and
# https://stackoverflow.com/a/38078544 because I'm some kind of lunatic and with help from @thegamecracks#1317 on
# the discord.py Discord server
class Postgres(object):

    def __init__(self):
        self._connection = psycopg2.connect(os.environ.get("DATABASE_URL"))
        self._cursor = self._connection.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    @property
    def connection(self):
        return self._connection

    @property
    def cursor(self):
        return self._cursor

    def commit(self):
        self._connection.commit()

    async def close(self, commit=True):
        if commit:
            self.commit()
        await self._connection.close()

    def execute(self, sql, params=None):
        self._cursor.execute(sql, params or ())
        self.commit()

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchone(self):
        return self._cursor.fetchone()

    def query(self, sql, params=None):
        self._cursor.execute(sql, params or ())
        return self.fetchall()

    def create_tables(self):
        # create prefix table
        self.execute("CREATE TABLE IF NOT EXISTS prefixes (guild_id BIGINT PRIMARY KEY, prefix VARCHAR(3) NOT NULL DEFAULT ';')")
        # create starboard table
        self.execute("CREATE TABLE IF NOT EXISTS starboard (guild_id BIGINT PRIMARY KEY, channel_id BIGINT NOT NULL, star_emoji VARCHAR NOT NULL DEFAULT '⭐', threshold INTEGER NOT NULL DEFAULT '3', confirm_emoji VARCHAR NOT NULL DEFAULT '🌟')")

