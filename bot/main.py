from typing import List

from telethon.sync import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from datetime import datetime, timedelta
from utils.config import API_ID, API_HASH
from datetime import datetime, timezone
from telethon.tl.functions.messages import ExportChatInviteRequest, GetDiscussionMessageRequest
from loguru import logger
from telethon.tl.types import PeerChannel

class TelegramBot:
    def __init__(self, phone_number, channel):
        self.client = TelegramClient(f'{phone_number}_session', API_ID, API_HASH)
        self.phone_number = phone_number
        self.channel = channel

    async def start(self):
        await self.client.start(self.phone_number)

    async def parse_all_members(self):
        async with self.client:
            id_ = None
            async for chat in self.client.iter_dialogs():
                if chat.name == self.channel:
                    id_ = chat.id
                    break
            print(id_)
            if id_ is not None:
                participants = await self.client.get_participants(id_)
                users = [{'id': user.id, 'username': user.username} for user in participants]
                return users
            else:
                print("Чат не найден")
                return []

    async def get_replies(self, hours, subscribers):
        async with self.client:
            id_ = None
            async for chat in self.client.iter_dialogs():
                if chat.name == self.channel:
                    id_ = chat.id
                    break
            replies: List[dict] = []
            timestamp_limit = datetime.now(timezone.utc) - timedelta(hours=hours)
            async for message in self.client.iter_messages(id_):
                if message.date >= timestamp_limit and message.replies:
                    message_id = message.id
            try:
                async for message in self.client.iter_messages(id_, reply_to=message_id):
                    if message.from_id != None:
                        for subscriber in subscribers:
                            if subscriber['id'] == message.from_id.__dict__['user_id']:
                                replies.append(subscriber)
                data = list(set(tuple(sorted(d.items())) for d in replies))
                result = [{k: v for k, v in item} for item in data]
                return result
            except Exception:
                logger.error(f'Постов {hours} часов назад не было.')

    async def parse_commenters(self):
        async with self.client:
            id_ = None
            async for chat in self.client.iter_dialogs():
                if chat.name == self.channel:
                    id_ = chat.id
                    break
        async with self.client:
            channel = await self.client.get_entity(id_)
            async for message in self.client.iter_messages(channel):
                if message.replies and message.replies.replies > 0:
                    discussion = await self.client(GetDiscussionMessageRequest(
                        peer=PeerChannel(channel.id),
                        msg_id=message.id
                    ))

                    if discussion and discussion.messages:
                        async for comment in self.client.iter_messages(discussion.messages[0].peer_id):
                            if comment.sender_id:
                                user = await self.client.get_entity(comment.sender_id)
                                print(f"Пользователь: {user.username or user.first_name}, ID: {user.id}")

    async def send_message_to_users(self, user_ids, message):
        async with self.client:
            for user_id in user_ids:
                try:
                    await self.client.send_message(user_id, message)
                except Exception as e:
                    print(f'Failed to send message to {user_id}: {e}')

    async def add_users_to_chat(self, user_ids):
        async with self.client:
            id_ = None
            async for chat in self.client.iter_dialogs():
                if chat.name == self.channel:
                    id_ = chat.id
                    break
        async with self.client:
            for user_id in user_ids:
                try:
                    await self.client(InviteToChannelRequest(id_, [user_id]))
                    logger.success(f'Юзер {user_id} добавлен в телеграмм канал {self.channel}')
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


    def run(self):
        self.client.loop.run_until_complete(self.start())


if __name__ == "__main__":
    phone_number = '89088935547'
    channel= 'CoinSpace - Трейдинг, новости, криптовалюта'

    bot = TelegramBot(phone_number, channel)
    bot.run()

    # members = bot.client.loop.run_until_complete(bot.parse_all_members())
    # logger.success(f'|| Все подписчики: {members}\n{len(members)}')

    # comments = bot.client.loop.run_until_complete(bot.get_replies( 800, members))
    # logger.success(f'|| Комментарии под постом оставили: {comments}')

    # comment = bot.client.loop.run_until_complete(bot.parse_commenters())

    # bot.client.loop.run_until_complete(bot.send_message_to_users([123456789, 987654321], "Hello from the bot!"))

    # bot.client.loop.run_until_complete(bot.add_users_to_chat([1932210797]))
