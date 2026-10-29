"""
Парсер для русского ассоциативного словаря-тезауруса
"""
import os
import re
from typing import Dict, List, Tuple

# Путь к словарю относительно папки проекта
DEFAULT_DICTIONARY_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'Русский Региональный Ассоциативный СловарьТезаурус.txt'
)


class DictionaryParser:
    """Класс для парсинга ассоциативного словаря"""

    def __init__(self, filepath: str = DEFAULT_DICTIONARY_PATH):
        self.filepath = filepath
        self.dictionary: Dict[str, List[Tuple[str, int]]] = {}

    def parse(self) -> Dict[str, List[Tuple[str, int]]]:
        """
        Парсит словарь и возвращает словарь формата:
        {
            'СЛОВО': [('ассоциация1', частота1), ('ассоциация2', частота2), ...]
        }
        """
        current_word = None

        with open(self.filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                # Пропускаем пустые строки и заголовки
                if not line or line.startswith('Г.А.') or line.startswith('РУССКИЙ'):
                    continue

                # Проверяем, является ли строка началом новой словарной статьи
                # Словарная статья начинается с ЗАГЛАВНОГО слова, за которым следует двоеточие
                if ':' in line and self._is_dictionary_entry(line):
                    # Разбираем словарную статью
                    word, associations = self._parse_entry(line)
                    if word and associations:
                        current_word = word
                        self.dictionary[current_word] = associations
                elif current_word and ';' in line:
                    # Продолжение предыдущей словарной статьи
                    additional_assoc = self._parse_continuation(line)
                    if additional_assoc:
                        self.dictionary[current_word].extend(additional_assoc)

        return self.dictionary

    def _is_dictionary_entry(self, line: str) -> bool:
        """Проверяет, является ли строка началом словарной статьи"""
        # Словарная статья обычно начинается с ЗАГЛАВНОГО слова или слова с заглавной буквы
        parts = line.split(':')
        if len(parts) < 2:
            return False

        word_candidate = parts[0].strip()

        # Проверяем, что это не продолжение текста и не служебная информация
        if any(keyword in word_candidate for keyword in ['том', 'Том', 'Структура', 'словаря']):
            return False

        return True

    def _parse_entry(self, line: str) -> Tuple[str, List[Tuple[str, int]]]:
        """
        Парсит одну словарную статью
        Формат: СЛОВО: ассоциация1 частота1; ассоциация2 частота2; ...
        """
        parts = line.split(':', 1)
        if len(parts) < 2:
            return None, []

        word = parts[0].strip()
        associations_str = parts[1].strip()

        associations = self._parse_associations(associations_str)

        return word, associations

    def _parse_continuation(self, line: str) -> List[Tuple[str, int]]:
        """Парсит продолжение словарной статьи"""
        return self._parse_associations(line)

    def _parse_associations(self, text: str) -> List[Tuple[str, int]]:
        """
        Парсит строку с ассоциациями
        Формат: ассоциация1, ассоциация2 частота; ассоциация3 частота; ...
        """
        associations = []

        # Разделяем по точке с запятой
        parts = text.split(';')

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Ищем последнее число в строке (это частота)
            # Используем регулярное выражение для поиска числа в конце
            match = re.search(r'\s+(\d+)\s*$', part)

            if match:
                frequency = int(match.group(1))
                # Всё, что до числа - это ассоциации (могут быть через запятую)
                assoc_text = part[:match.start()].strip()

                # Разделяем ассоциации по запятой
                assoc_list = [a.strip() for a in assoc_text.split(',') if a.strip()]

                # Каждая ассоциация в группе имеет одинаковую частоту
                for assoc in assoc_list:
                    associations.append((assoc, frequency))
            elif part and not part.endswith('+'):
                # Если нет числа и это не статистическая строка
                # проверяем, не является ли это частью формата "слово1, слово2, словоN число"
                continue

        return associations

    def get_words(self) -> List[str]:
        """Возвращает список всех слов в словаре"""
        return list(self.dictionary.keys())

    def get_associations(self, word: str) -> List[Tuple[str, int]]:
        """Возвращает список ассоциаций для заданного слова"""
        return self.dictionary.get(word, [])

    def get_word_count(self) -> int:
        """Возвращает количество слов в словаре"""
        return len(self.dictionary)


if __name__ == '__main__':
    # Тестирование парсера
    parser = DictionaryParser()
    dictionary = parser.parse()

    print(f"Загружено слов: {parser.get_word_count()}")

    # Проверяем несколько слов
    test_words = ['АБСОЛЮТНЫЙ', 'АВТОМАТ']
    for word in test_words:
        if word in dictionary:
            assoc = parser.get_associations(word)
            print(f"\n{word}: {len(assoc)} ассоциаций")
            print(f"Топ-5 ассоциаций: {assoc[:5]}")
