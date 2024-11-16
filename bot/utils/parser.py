import asyncio
import os
from typing import List, Optional

from telethon.sync import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from datetime import datetime, timedelta
from bot.utils.config import API_ID, API_HASH
from datetime import datetime, timezone
from telethon.tl.types import Chat, Channel
from telethon.tl.functions.messages import ExportChatInviteRequest, GetDiscussionMessageRequest
from loguru import logger
from telethon.tl.functions.messages import GetRepliesRequest
from telethon.errors import FloodWaitError
from telethon.errors.rpcerrorlist import RPCError, MsgIdInvalidError
from telethon.tl.functions.messages import GetMessageReactionsListRequest
from telethon.tl.types.auth import SentCode
from telethon.errors import UserIdInvalidError
from telethon import connection



class TelegramBot:
    def __init__(self, session):
        self.session = session
        self.client = TelegramClient(f'{session}', API_ID, API_HASH)

    async def start(self):
        await self.client.start()

    async def _get_chat_id(self, channel_link):
        async with self.client:
            try:
                entity = await self.client.get_entity(channel_link)
                return entity.id
            except Exception as e:
                logger.error(f"Failed to resolve channel link {channel_link}: {e}")
                return None

    async def parse_users_from_comments(self, channel_link, is_both_work: Optional[bool] = None, hours=None):
        end_time = datetime.now(timezone.utc)
        start_time = datetime.min.replace(tzinfo=timezone.utc) if hours is None else (end_time - timedelta(hours=hours))

        users_commented = []

        try:
            id_ = await self._get_chat_id(channel_link)
            if id_ is None:
                logger.error("Invalid channel link.")
                return None
            if is_both_work == False:
                async with self.client:
                    async for message in self.client.iter_messages(id_):
                        if hours is not None and message.date < start_time:
                            break
                        try:
                            if message.date <= end_time and not message.is_reply:
                                async for comment in self.client.iter_messages(id_, reply_to=message.id):
                                    try:
                                        if start_time <= comment.date <= end_time:
                                            user_info = {
                                                'id': comment.sender_id,
                                                'username': comment.sender.username if comment.sender else 'None'
                                            }
                                            if user_info not in users_commented:
                                                users_commented.append(user_info)
                                    except FloodWaitError as e:
                                        logger.error(f"Flood wait error. Sleeping for {e.seconds} seconds.")
                                        await asyncio.sleep(e.seconds)
                                    except RPCError as rpc_error:
                                        logger.error(f"RPC error occurred: {rpc_error}")
                                    except Exception as e:
                                        logger.error(f"Error processing comment: {e}")
                                        await asyncio.sleep(1)
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            await asyncio.sleep(3)

                file_path = 'commenters_from_channel.txt'
                with open(file_path, 'w', encoding='utf-8') as file:
                    for user in users_commented:
                        file.write(f"{user['id']}: {user['username']}\n")

                return file_path
            else:
                async with self.client:
                    async for message in self.client.iter_messages(id_):
                        if hours is not None and message.date < start_time:
                            break
                        try:
                            if message.date <= end_time and not message.is_reply:
                                async for comment in self.client.iter_messages(id_, reply_to=message.id):
                                    try:
                                        if start_time <= comment.date <= end_time:
                                            user_info = {
                                                'id': comment.sender_id,
                                                'username': comment.sender.username if comment.sender else 'None'
                                            }
                                            if user_info not in users_commented:
                                                users_commented.append(user_info)
                                    except FloodWaitError as e:
                                        logger.error(f"Flood wait error. Sleeping for {e.seconds} seconds.")
                                        await asyncio.sleep(e.seconds)
                                    except RPCError as rpc_error:
                                        logger.error(f"RPC error occurred: {rpc_error}")
                                    except Exception as e:
                                        logger.error(f"Error processing comment: {e}")
                                        await asyncio.sleep(1)
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            await asyncio.sleep(3)

                result = ''
                for user in users_commented:
                    result += f"{user['id']}\n"

                return result


        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return None

    async def parse_chat_members(self, channel_link, is_both_work: Optional[bool] = None):
        id_ = await self._get_chat_id(channel_link)
        if id_ is None:
            logger.error("Invalid channel link.")
            return None
        if is_both_work == False:
            async with self.client:
                participants = await self.client.get_participants(id_)

                output_file = 'chat_members.txt'

                with open(output_file, 'w', encoding='utf-8') as file:
                    for participant in participants:
                        if participant.username:
                            file.write(f"{participant.id}: {participant.username}\n")
                        else:
                            file.write(f"{participant.id}: None\n")

                logger.success(f"Данные участников сохранены в {output_file}")
            return output_file
        else:
            async with self.client:
                participants = await self.client.get_participants(id_)

                members = ''

                for participant in participants:
                    members += f"{participant.id}\n"
                logger.success(f"Данные участников сохранены")
            return members

    async def get_active_users(self, channel_link, hours, is_both_work: Optional[bool] = None,  output_file='chat_active_users.txt'):
        start_time = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
        active_users = {}
        id_ = await self._get_chat_id(channel_link)
        if id_ is None:
            logger.error("Invalid channel link.")
            return None
        if is_both_work == False:
            async with self.client:
                async for message in self.client.iter_messages(id_):
                    if message.date >= start_time:
                        if message.sender_id and message.sender_id not in active_users:
                            try:
                                user = await self.client.get_entity(message.sender_id)
                                username = user.username if user.username else 'N/A'
                                active_users[message.sender_id] = username
                            except Exception:
                                pass
                    else:
                        break

            with open(output_file, 'w') as file:
                for user_id, username in active_users.items():
                    file.write(f'{user_id}: {username}\n')

            logger.success(f'Данные сохранены в файл {output_file}')

            return output_file
        else:
            async with self.client:
                async for message in self.client.iter_messages(id_):
                    if message.date >= start_time:
                        if message.sender_id and message.sender_id not in active_users:
                            try:
                                user = await self.client.get_entity(message.sender_id)
                                username = user.username if user.username else 'N/A'
                                active_users[message.sender_id] = username
                            except Exception:
                                pass
                    else:
                        break

            result = ''
            for user_id, username in active_users.items():
                result += f'{user_id}\n'

            logger.success(f'Данные сохранены')

            return result

    async def get_users_with_reactions(self, channel_link, hours, is_both_work: Optional[bool] = None, output_file='reactions_users.txt'):
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
        users = {}
        id_ = await self._get_chat_id(channel_link)
        if id_ is None:
            logger.error("Invalid channel link.")
            return None
        if is_both_work == False:
            async with self.client:
                async for message in self.client.iter_messages(id_):
                    if message.date < time_threshold:
                        break

                    if message.reactions and message.reactions.recent_reactions:
                        for reaction in message.reactions.recent_reactions:
                            user_id = reaction.peer_id.user_id
                            try:
                                user = await self.client.get_entity(user_id)
                                username = user.username if user.username else "None"
                            except (UserIdInvalidError, ValueError):
                                username = "None"

                            if user_id not in users:
                                users[user_id] = username

            with open(output_file, 'w', encoding='utf-8') as file:
                for user_id, username in users.items():
                    file.write(f"{user_id}: {username}\n")

            logger.success(f"Данные сохранены в файл: {output_file}")
            return os.path.abspath(output_file)
        else:
            async with self.client:
                async for message in self.client.iter_messages(id_):
                    if message.date < time_threshold:
                        break

                    if message.reactions and message.reactions.recent_reactions:
                        for reaction in message.reactions.recent_reactions:
                            user_id = reaction.peer_id.user_id
                            try:
                                user = await self.client.get_entity(user_id)
                                username = user.username if user.username else "None"
                            except (UserIdInvalidError, ValueError):
                                username = "None"

                            if user_id not in users:
                                users[user_id] = username
            result = ''
            for user_id, username in users.items():
                result += f"{user_id}\n"

            logger.success(f"Данные сохранены")
            return result

    async def chat_and_group(self, link, hours):
        try:
            result = await self.parse_chat_members(link, is_both_work=True)
            result1 = await self.get_active_users(link, hours, is_both_work=True)
            result2 = await self.get_users_with_reactions(link, hours, is_both_work=True)
            list_ = (result + result1 + result2).split('\n')
            return '\n'.join(list(set(list_)))
        except Exception:
            result = await self.parse_users_from_comments(link, is_both_work=True,  hours=hours)
            return result

    async def send_message_to_users(self, user_ids, message):
        async with self.client:
            for user_id in user_ids:
                try:
                    await self.client.send_message(user_id, message)
                except Exception as e:
                    logger.error(f'Failed to send message to {user_id}: {e}')

    async def add_users_to_chat(self, channel_link, user_ids):
        id_ = await self._get_chat_id(channel_link)
        if id_ is None:
            logger.error("Invalid channel link.")
            return None

        async with self.client:
            for user_id in user_ids:
                try:
                    await self.client(InviteToChannelRequest(id_, [user_id]))
                    logger.success(f'Юзер {user_id} добавлен в телеграмм канал {channel_link}')
                except Exception:
                    try:
                        logger.error('Человек запретил себя добавлять в сторонние телеграмм каналы')
                        invite = await self.client(ExportChatInviteRequest(peer=id_))
                        invite_link = invite.link
                        message_text = f'Привет! Присоединяйся к нашему каналу по этой ссылке: {invite_link}'
                        await self.client.send_message(entity=user_id, message=message_text)
                        logger.success(f'Ссылка-приглашение успешно отправлена пользователю {user_id}')
                    except Exception:
                        logger.error(f'Не удалось отправить сообщение человеку с {user_id}')



# if __name__ == "__main__":
    # phone_number = '89088935547'
    # channel= 'Teams Pain ЧАТ'

    # bot = TelegramBot(phone_number)
    # bot.run()

    # members = bot.client.loop.run_until_complete(bot.parse_users_from_comments())
    # logger.success(f'|| Все подписчики: {members}\n{len(members)}')

    # comments = bot.client.loop.run_until_complete(bot.parse_chat_members())
    # logger.success(f'|| {comments}')

    # active_users = bot.client.loop.run_until_complete(bot.get_active_users(40))

    # reactions = bot.client.loop.run_until_complete(bot.get_users_with_reactions(channel,50))

    # bot.client.loop.run_until_complete(bot.send_message_to_users([123456789, 987654321], "Hello from the bot!"))

    # bot.client.loop.run_until_complete(bot.add_users_to_chat([1932210797]))



