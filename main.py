'''
Inactivity Tracker Module

Copyright (C) 2024  __retr0.init__

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import interactions

"Highly recommended - we suggest providing proper debug logging"
from src import logutil

from typing import Optional, cast, Generator

# Import the os module to get the parent path to the local files
import os
# aiofiles module is recommended for file operation
import aiofiles
# You can listen to the interactions.py event
from interactions.api.events import MessageCreate
# You can create a background task
from interactions import Task, IntervalTrigger

from collections import namedtuple

logger = logutil.init_logger(os.path.basename(__file__))

"""
The judge pause period in hour.
It is like updating the latest time that a user's message every `JUDGING_HOUR` hours.
It also adds to the judgeing time to temporarily remove roles from the user.
"""
JUDGING_HOUR: int = 24

"""
DB is updated with new values. Need to commit the changes in periodic task
"""
DB_updated: bool = False

"""
Whether the DB is initialised. It's to judge whether all info is aquired for judging and execution
"""
data_initialised: bool = False

class ChannelHistoryIteractor:
    def __init__(self, history: interactions.ChannelHistory):
        self.history: interactions.ChannelHistory = history

    def __aiter__(self):
        return self
    
    async def __anext__(self):
        try:
            return await self.history.__anext__()
        except StopAsyncIteration:
            raise StopAsyncIteration
        except interactions.errors.HTTPException as e:
            try:
                match int(e.code):
                    case 50083:
                        """Operation in archived thread"""
                        logger.error(f"Channel {self.history.channel.name} ({self.history.channel.id}) is an archived thread")
                        raise StopAsyncIteration
                    case 10003:
                        """Unknown channel"""
                        logger.error(f"Operating in an unknown channel")
                        raise StopAsyncIteration
                    case 10008:
                        """Unknown message"""
                        logger.warning(f"Unknown message in Channel {self.history.channel.name} ({self.history.channel.id})")
                        pass
                    case 50001:
                        """No Access"""
                        logger.error(f"Bot has no access to Channel {self.history.channel.name} ({self.history.channel.id})")
                        raise StopAsyncIteration
                    case 50013:
                        """Lack permission"""
                        logger.error(f"Channel {self.history.channel.name} ({self.history.channel.id}) lacks permission")
                        raise StopAsyncIteration
                    case 50021:
                        """Cannot execute on system message"""
                        logger.warning(f"System message in Channel {self.history.channel.name} ({self.history.channel.id})")
                        pass
                    case 160005:
                        """Thread is locked"""
                        logger.warning(f"Channel {self.history.channel.name} ({self.history.channel.id}) is a locked thread")
                        pass
                    case _:
                        """Default"""
                        logger.warning(f"Channel {self.history.channel.name} ({self.history.channel.id}) has unknown code {e.code}")
                        pass
            except ValueError:
                logger.warning(f"Unknown HTTP exception {e.code} {e.errors} {e.route} {e.response} {e.text}")
                pass
        except Exception as e:
            logger.warning(f"Unknown exception {e.code} {e.errors} {e.route} {e.response} {e.text}")
            pass

# async def search_latest_msg_ch(user_id: int, channel: interactions.MessageableMixin) -> Optional[interactions.Message]:
#     """
#     Find the latest message of a user in a channel. If no message is found, return None
#     """
#     result: Optional[interactions.Message] = None
#     history: interactions.ChannelHistory = channel.history(0)
#     async for msg in ChannelHistoryIteractor(history=history):
#         if msg.author.id == user_id:
#             result = msg
#             break
#     return result

UserTime = namedtuple("UserTime", "user time index")

Mem_UserTimes: list[UserTime] = []

async def fetch_list_user_latest_msg_ch(channel: interactions.MessageableMixin) -> list[UserTime]:
    """
    Get the list of (user, time) for the latest message in a channel
    """
    result: list[UserTime] = []
    history: interactions.ChannelHistory = channel.history(0)
    async for msg in ChannelHistoryIteractor(history=history):
        if msg.author.id not in (r.user for r in result):
            tt = msg.edited_timestamp if msg.edited_timestamp else msg.timestamp
            result.append(UserTime(msg.author.id, tt.timestamp(), len(result)))
    return result

def merge_list_usertime_latest(usertimess: list[list[UserTime]]) -> list[UserTime]:
    """
    Merge lists of list of usertime with the latest time
    """
    result: list[UserTime] = []
    found: bool = False
    for usertimes in usertimess:
        for ut in usertimes:
            found = False
            for i, res_ut in enumerate(result):
                if ut.user == res_ut.user:
                    found = True
                    if ut.time < res_ut.time:
                        result[i] = UserTime(res_ut.user, res_ut.time, i)
                    break
            if not found:
                result.append(UserTime(ut.user, ut.time, len(result)))
    return result

def filter_usertime_time(usertimes: list[UserTime], timestamp: float) -> Generator[UserTime]:
    """
    Filter usertime list before (less than) given timestamp. It skips the JUDGING_HOUR for filtering.
    """
    result: Generator[UserTime] = (usertime for usertime in usertimes if usertime.time < (timestamp - JUDGING_HOUR*60*60))
    return result

"""
TODO add local database storage support
TODO record all the taken roles if the user's roles are stripped
TODO restore the recorded roles to the user if thy sends a message
TODO validate whether the role still exists before applying them
TODO add configuration storage
TODO add startup pickup commands
TODO add configuration commands
TODO add status command
TODO show users to be executed
"""

'''
Replace the ModuleName with any name you'd like
'''
class Retr0InitInactivityTrack(interactions.Extension):
    module_base: interactions.SlashCommand = interactions.SlashCommand(
        name="inactivity",
        description="Inactivity tracking module"
    )
    module_group: interactions.SlashCommand = module_base.group(
        name="setting",
        description="Configure the inactivity tracker module"
    )

    @module_group.subcommand("ping", sub_cmd_description="Replace the description of this command")
    @interactions.slash_option(
        name = "option_name",
        description = "Option description",
        required = True,
        opt_type = interactions.OptionType.STRING
    )
    async def module_group_ping(self, ctx: interactions.SlashContext, option_name: str):
        await ctx.send(f"Pong {option_name}!")
        internal_t.internal_t_testfunc()

    @module_base.subcommand("pong", sub_cmd_description="Replace the description of this command")
    @interactions.slash_option(
        name = "option_name",
        description = "Option description",
        required = True,
        opt_type = interactions.OptionType.STRING
    )
    async def module_group_pong(self, ctx: interactions.SlashContext, option_name: str):
        # The local file path is inside the directory of the module's main script file
        async with aiofiles.open(f"{os.path.dirname(__file__)}/example_file.txt") as afp:
            file_content: str = await afp.read()
        await ctx.send(f"Pong {option_name}!\nFile content: {file_content}")
        internal_t.internal_t_testfunc()

    @interactions.listen(MessageCreate)
    async def on_messagecreate(self, event: MessageCreate):
        '''
        Event listener when a new message is created
        '''
        print(f"User {event.message.author.display_name} sent '{event.message.content}'")
        ut: Optional[UserTime] = next((x for x in Mem_UserTimes if x.user == event.message.id), None)
        if not ut:
            Mem_UserTimes.append(UserTime(
                event.message.author.id, 
                event.message.timestamp.timestamp(),
                len(Mem_UserTimes)))
            return
        if ut.time + JUDGING_HOUR * 3600 <= event.message.timestamp.timestamp():
            Mem_UserTimes[ut.index] = UserTime(ut.user, event.message.timestamp.timestamp(), ut.index)
            #TODO Write to database
    
    @Task.create(IntervalTrigger(minutes=10))
    async def task_db_commit(self):
        if DB_updated:
            #TODO Commit the DB changes
            pass

    # You can even create a background task to run as you wish.
    # Refer to https://interactions-py.github.io/interactions.py/Guides/40%20Tasks/ for guides
    # Refer to https://interactions-py.github.io/interactions.py/API%20Reference/API%20Reference/models/Internal/tasks/ for detailed APIs
    @Task.create(IntervalTrigger(minutes=1))
    async def task_everyminute(self):
        channel: interactions.TYPE_MESSAGEABLE_CHANNEL = self.bot.get_guild(1234567890).get_channel(1234567890)
        await channel.send("Background task send every one minute")
        print("Background Task send every one minute")

    # The command to start the task
    @module_base.subcommand("start_task", sub_cmd_description="Start the background task")
    async def module_base_starttask(self, ctx: interactions.SlashContext):
        self.task_everyminute.start()
        await ctx.send("Task started")