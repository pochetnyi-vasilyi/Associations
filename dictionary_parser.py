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

# Начало словарной статьи: СТИМУЛ заглавными буквами и двоеточие
ENTRY_RE = re.compile(r'^([А-ЯЁA-Z][А-ЯЁA-Z \-]*):\s*(.*)$')
# Конец словарной статьи: итоговые показатели вида 538+201+18+135
STATS_RE = re.compile(r'\d+\+\d+\+\d+\+\d+\s*$')
# Номер страницы на отдельной строке
PAGE_NUMBER_RE = re.compile(r'^\d+$')


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
        entry_lines = []

        with open(self.filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                # Пропускаем пустые строки и номера страниц
                if not line or PAGE_NUMBER_RE.match(line):
                    continue

                match = ENTRY_RE.match(line)
                if match:
                    # Начало новой словарной статьи
                    current_word = match.group(1).strip()
                    entry_lines = [match.group(2)]
                elif current_word:
                    # Продолжение текущей статьи
                    entry_lines.append(line)
                else:
                    # Титул, вступление и буквы-разделители между статьями
                    continue

                # Статья заканчивается итоговыми показателями
                if STATS_RE.search(line):
                    text = STATS_RE.sub('', self._join_lines(entry_lines))
                    self.dictionary[current_word] = self._parse_associations(text)
                    current_word = None

        return self.dictionary

    def _join_lines(self, lines: List[str]) -> str:
        """Склеивает строки статьи; после дефиса перенос без пробела (по-/любому)"""
        text = ''
        for line in lines:
            if not text or text.endswith('-'):
                text += line
            else:
                text += ' ' + line
        return text

    def _parse_associations(self, text: str) -> List[Tuple[str, int]]:
        """
        Парсит текст статьи с ассоциациями
        Формат: ассоциация1, ассоциация2 частота; ассоциация3 частота; ...
        """
        associations = []
        # Ассоциации из кусков без частоты (в словаре ';' вместо ',')
        # получают частоту следующей группы
        pending = []

        for part in text.split(';'):
            part = part.strip()
            if not part:
                continue

            # Частота - число в конце группы
            match = re.search(r'\s(\d+)$', part)

            if match:
                frequency = int(match.group(1))
                # Каждая ассоциация в группе имеет одинаковую частоту
                for assoc in pending + self._split_group(part[:match.start()]):
                    associations.append((assoc, frequency))
                pending = []
            else:
                pending.extend(self._split_group(part))

        return associations

    def _split_group(self, text: str) -> List[str]:
        """Делит группу по запятым; {,} - запятая внутри самой ассоциации"""
        return [a.strip().replace('\0', ',') for a in text.replace('{,}', '\0').split(',') if a.strip()]

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
