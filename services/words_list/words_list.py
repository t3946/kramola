from abc import abstractmethod
from typing import TypedDict, Dict, List, Any
from datetime import datetime, date
from enum import Enum
import json
from services.redis.connection import get_redis_connection
from services.fulltext_search.phrase import Phrase

# from flask import (current_app as app)

# Get Redis connection (bytes mode for compatibility with existing code)
r = get_redis_connection(decode_responses=False)


class PredefinedListKey(str, Enum):
    FOREIGN_AGENTS_PERSONS = "foreign_agents_persons"
    FOREIGN_AGENTS_COMPANIES = "foreign_agents_companies"
    PROFANITY = "profanity"
    PROHIBITED_SUBSTANCES = "prohibited_substances"
    SWEAR_WORDS = "swear_words"

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

        phrases_list: List[Phrase] = [Phrase(word) for word in words_list]

        if logging:
            phrases_list_old = self.load()
            phrases_old_texts = {phrase.phrase for phrase in phrases_list_old}
            phrases_new_texts = {phrase.phrase for phrase in phrases_list}
            added_words = list(phrases_new_texts - phrases_old_texts)
            deleted_words = list(phrases_old_texts - phrases_new_texts)
            now = datetime.now()
            date = now.strftime('%Y-%m-%d')

            key_deleted_words = self.get_log_key(f'{date}:deleted')
            key_added_words = self.get_log_key(f'{date}:added')
            r.delete(key_deleted_words)
            r.delete(key_added_words)

            if deleted_words:
                r.rpush(key_deleted_words, *[word.encode('utf-8') for word in deleted_words])

            if added_words:
                r.rpush(key_added_words, *[word.encode('utf-8') for word in added_words])

        r.delete(key_list)
        phrases_json = [phrase.to_json().encode('utf-8') for phrase in phrases_list]
        r.rpush(key_list, *phrases_json)

    def load(self) -> List[Phrase]:
        list_key = self.get_list_key()
        stored_list = r.lrange(list_key, 0, -1)
        phrases: List[Phrase] = []

        for item in stored_list:
            json_str = item.decode('utf-8')
            phrase = Phrase.from_json(json_str)
            phrases.append(phrase)
        
        return phrases

    def clear(self):
        list_key = self.get_list_key()
        r.delete(list_key)
        self.clear_log()

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

    def get_changes_json(self) -> Dict[str, Dict[str, Any]]:
        logs_by_date = self.load_logs()
        result = {}
        
        for date_str, changes in logs_by_date.items():
            # Parse date string to date object
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            result[date_str] = {
                'date': date_obj,
                'added': changes.get('added', []),
                'deleted': changes.get('deleted', []),
                'added_count': len(changes.get('added', [])),
                'deleted_count': len(changes.get('deleted', []))
            }
        
        return result

    def clear_log(self, dates: str = None) -> None:
        if dates is None:
            pattern = self.get_log_key('*')
            keys_to_delete = [key for key in r.scan_iter(pattern)]
        else:
            keys_to_delete = []

            for date in dates:
                keys_to_delete.extend([
                    self.get_log_key(f"{date}:added").encode('utf-8'),
                    self.get_log_key(f"{date}:deleted").encode('utf-8')
                ])

        if keys_to_delete:
            r.unlink(*keys_to_delete)
