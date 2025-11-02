"""
Основная логика игры "Ассоциации"
"""
import random
from typing import Dict, List, Tuple
from enum import Enum


class Difficulty(Enum):
    """Уровни сложности игры"""
    EASY = 1
    MEDIUM = 2
    HARD = 3
    EXPERT = 4


class GameConfig:
    """Конфигурация для каждого уровня сложности"""

    CONFIGS = {
        Difficulty.EASY: {
            'associations_count': 5,
            'attempts': 5,
            'use_frequent': True,  # Использовать самые частые ассоциации
            'min_frequency': 5,    # Минимальная частота ассоциаций
            'multiplier': 1
        },
        Difficulty.MEDIUM: {
            'associations_count': 4,
            'attempts': 4,
            'use_frequent': True,
            'min_frequency': 3,
            'multiplier': 2
        },
        Difficulty.HARD: {
            'associations_count': 3,
            'attempts': 3,
            'use_frequent': False,  # Использовать любые ассоциации
            'min_frequency': 2,
            'multiplier': 3
        },
        Difficulty.EXPERT: {
            'associations_count': 2,
            'attempts': 2,
            'use_frequent': False,
            'min_frequency': 1,
            'multiplier': 5
        }
    }

    @staticmethod
    def get_config(difficulty: Difficulty) -> Dict:
        """Получить конфигурацию для уровня сложности"""
        return GameConfig.CONFIGS[difficulty]


class AssociationsGame:
    """Основной класс игры"""

    def __init__(self, dictionary: Dict[str, List[Tuple[str, int]]]):
        self.dictionary = dictionary
        self.current_word = None
        self.current_associations = []
        self.shown_associations = []
        self.difficulty = Difficulty.EASY
        self.attempts_left = 0
        self.score = 0
        self.hints_used = 0

    def start_new_round(self, difficulty: Difficulty = Difficulty.EASY) -> bool:
        """
        Начать новый раунд игры
        Возвращает True если раунд успешно начат, False если нет подходящих слов
        """
        self.difficulty = difficulty
        config = GameConfig.get_config(difficulty)

        # Выбираем случайное слово с достаточным количеством ассоциаций
        suitable_words = self._get_suitable_words(config)

        if not suitable_words:
            return False

        self.current_word = random.choice(suitable_words)
        self.attempts_left = config['attempts']
        self.hints_used = 0

        # Получаем ассоциации для текущего слова
        all_associations = self.dictionary[self.current_word]

        # Фильтруем ассоциации по минимальной частоте
        filtered_associations = [
            (assoc, freq) for assoc, freq in all_associations
            if freq >= config['min_frequency']
        ]

        # Выбираем ассоциации в зависимости от уровня сложности
        if config['use_frequent']:
            # Сортируем по убыванию частоты и берём самые частые
            filtered_associations.sort(key=lambda x: x[1], reverse=True)
        else:
            # Берём случайные, включая редкие
            random.shuffle(filtered_associations)

        # Выбираем нужное количество ассоциаций
        self.current_associations = filtered_associations[:config['associations_count']]

        # Показываем ассоциации постепенно (сначала самые редкие)
        self.current_associations.sort(key=lambda x: x[1])
        self.shown_associations = []

        return True

    def _get_suitable_words(self, config: Dict) -> List[str]:
        """Получить список слов, подходящих для текущей сложности"""
        suitable_words = []

        for word, associations in self.dictionary.items():
            # Фильтруем ассоциации по минимальной частоте
            valid_associations = [
                assoc for assoc, freq in associations
                if freq >= config['min_frequency']
            ]

            # Слово подходит, если у него достаточно ассоциаций
            if len(valid_associations) >= config['associations_count']:
                suitable_words.append(word)

        return suitable_words

    def reveal_next_association(self) -> Tuple[str, int] | None:
        """
        Открыть следующую ассоциацию
        Возвращает (ассоциация, частота) или None если все уже открыты
        """
        if len(self.shown_associations) < len(self.current_associations):
            next_assoc = self.current_associations[len(self.shown_associations)]
            self.shown_associations.append(next_assoc)
            return next_assoc
        return None

    def get_hint(self) -> str | None:
        """
        Получить подсказку (первую букву слова)
        Уменьшает итоговый счёт
        """
        if self.current_word:
            self.hints_used += 1
            # Показываем первые N букв в зависимости от количества использованных подсказок
            hint_length = min(self.hints_used, len(self.current_word) - 1)
            return self.current_word[:hint_length] + '...'
        return None

    def make_guess(self, guess: str) -> Tuple[bool, int]:
        """
        Сделать попытку угадать слово
        Возвращает (правильно ли угадано, полученные очки)
        """
        self.attempts_left -= 1

        # Нормализуем ввод для сравнения
        guess_normalized = guess.strip().upper()
        correct = guess_normalized == self.current_word.upper()

        if correct:
            points = self._calculate_score()
            self.score += points
            return True, points

        return False, 0

    def _calculate_score(self) -> int:
        """Рассчитать очки за правильный ответ"""
        config = GameConfig.get_config(self.difficulty)

        # Базовые очки: попытки × сложность × 100
        base_score = self.attempts_left * config['multiplier'] * 100

        # Бонус за угадывание с первой попытки
        if self.attempts_left == config['attempts'] - 1:
            base_score += 500

        # Штраф за использование подсказок
        penalty = self.hints_used * 100

        return max(0, base_score - penalty)

    def get_game_state(self) -> Dict:
        """Получить текущее состояние игры"""
        return {
            'word': self.current_word,
            'difficulty': self.difficulty.name,
            'attempts_left': self.attempts_left,
            'shown_associations': self.shown_associations,
            'total_associations': len(self.current_associations),
            'score': self.score,
            'hints_used': self.hints_used
        }

    def is_game_over(self) -> bool:
        """Проверить, закончилась ли игра (кончились попытки)"""
        return self.attempts_left <= 0

    def get_current_word(self) -> str:
        """Получить текущее загаданное слово (для отладки или показа после проигрыша)"""
        return self.current_word

    def get_total_score(self) -> int:
        """Получить общий счёт"""
        return self.score
