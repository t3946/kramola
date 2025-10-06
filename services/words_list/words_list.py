from abc import  abstractmethod
from typing import TypedDict
from datetime import datetime

import redis

class TSaveOptions(TypedDict):
    logging: bool

class WordsList:
    KEY_PREFIX = 'words_list_'
    # unique list key
    @property
    @abstractmethod
    def list_key(self):
        pass

    def save(self, words_list: list[str], options: TSaveOptions) -> None:
        r = redis.Redis(host='localhost', port=6379, db=0)
        key_list = WordsList.KEY_PREFIX + self.list_key

        if options.logging:
            words_list_old = self.load()
            deleted_words = list(set(words_list) - set(words_list_old))
            added_words = list(set(words_list_old) - set(words_list))
            now = datetime.now()
            date = now.strftime('%Y-%m-%d')
            key_deleted_words = key_list + f":log:{date}:deleted"
            key_added_words = key_list + f":log:{date}:added"
            r.rpush(key_deleted_words, *deleted_words)
            r.rpush(key_added_words, *added_words)


        r.delete(key_list)
        r.rpush(key_list, *words_list)
        print()

    def load(self) -> list[str]:
        r = redis.Redis(host='localhost', port=6379, db=0)
        list_key = self.KEY_PREFIX + self.list_key
        stored_list = r.lrange(list_key, 0, -1)  # получить весь список
        # элементы возвращаются как байты, декодируем в строки
        return [item.decode('utf-8') for item in stored_list]