from abc import abstractmethod
from typing import TypedDict, Dict, List
from datetime import datetime

from pandas.core.indexes.base import trim_front

from services.redis import r

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

    def get_list_key(self):
        return self.KEY_PREFIX + self.list_key

    def get_log_key(self, sub_key=''):
        key = self.get_list_key() + ':logs'

        if sub_key:
            key += ':' + sub_key

        return key

    def save(self, words_list: list[str], logging) -> None:
        key_list = WordsList.KEY_PREFIX + self.list_key

        if logging:
            words_list_old = self.load()
            deleted_words = list(set(words_list) - set(words_list_old))
            added_words = list(set(words_list_old) - set(words_list))
            now = datetime.now()
            date = now.strftime('%Y-%m-%d')

            key_deleted_words = key_list + self.get_log_key(f'{date}:deleted')
            key_added_words = key_list + self.get_log_key(f'{date}:added')
            r.rpush(key_deleted_words, *deleted_words)
            r.rpush(key_added_words, *added_words)

        r.delete(key_list)
        r.rpush(key_list, *words_list)
        print()

    def load(self) -> list[str]:
        list_key = self.get_list_key()
        stored_list = r.lrange(list_key, 0, -1)  # получить весь список
        # элементы возвращаются как байты, декодируем в строки
        return [item.decode('utf-8') for item in stored_list]

    def load_logs(self) -> Dict[str, Dict[str, List[str]]]:
        key_logs_pattern = self.get_log_key('*')
        logs_by_date = {}

        for key in r.scan_iter(key_logs_pattern):
            key_str = key.decode('utf-8')
            parts = key_str.split(':')
            date = parts[2]
            log_type = parts[3]
            log_list = r.lrange(key, 0, -1)
            log_list_decoded = [item.decode('utf-8') for item in log_list]

            if date not in logs_by_date:
                logs_by_date[date] = {'added': [], 'deleted': []}

            logs_by_date[date][log_type] = log_list_decoded

        return logs_by_date

    def clear_log(self, dates: str):
        if dates is None:
            # Удаляем все ключи с шаблоном ":log:*"
            pattern = self.get_log_key('*')
            keys_to_delete = [key for key in r.scan_iter(pattern)]
        else:
            # Составляем список ключей для указанных дат
            keys_to_delete = []

            for date in dates:
                keys_to_delete.extend([
                    self.get_log_key(f"{date}:added").encode('utf-8'),
                    self.get_log_key(f"{date}:deleted").encode('utf-8')
                ])

        if keys_to_delete:
            r.unlink(*keys_to_delete)
