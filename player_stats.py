"""
Система персистенции результатов игроков
"""
import json
import os
from datetime import datetime
from typing import Dict, List

# Путь к файлу статистики относительно папки проекта
DEFAULT_STATS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'player_stats.json')

DIFFICULTIES = ('EASY', 'MEDIUM', 'HARD', 'EXPERT')
COUNTERS = ('total_score', 'games_played', 'games_won', 'games_lost', 'best_score')


class StatsImportError(Exception):
    """Файл нельзя импортировать: не прочитан или не в формате статистики"""


def _is_count(value) -> bool:
    """Целое неотрицательное число (bool не считается)"""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


class PlayerStats:
    """Класс для управления статистикой игроков"""

    def __init__(self, stats_file: str = DEFAULT_STATS_PATH):
        self.stats_file = stats_file
        self.stats = self._load_stats()

    def _load_stats(self) -> Dict:
        """Загрузить статистику из файла"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {'players': {}}
        return {'players': {}}

    def _save_stats(self):
        """Сохранить статистику в файл"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Ошибка при сохранении статистики: {e}")

    def add_player(self, player_name: str):
        """Добавить нового игрока"""
        if player_name not in self.stats['players']:
            self.stats['players'][player_name] = {
                'total_score': 0,
                'games_played': 0,
                'games_won': 0,
                'games_lost': 0,
                'best_score': 0,
                'difficulty_stats': {
                    'EASY': {'played': 0, 'won': 0},
                    'MEDIUM': {'played': 0, 'won': 0},
                    'HARD': {'played': 0, 'won': 0},
                    'EXPERT': {'played': 0, 'won': 0}
                },
                'history': []
            }
            self._save_stats()

    def record_game(self, player_name: str, difficulty: str, won: bool, score: int, word: str):
        """
        Записать результат игры

        Args:
            player_name: Имя игрока
            difficulty: Уровень сложности (EASY, MEDIUM, HARD, EXPERT)
            won: Выиграл ли игрок
            score: Полученные очки
            word: Загаданное слово
        """
        if player_name not in self.stats['players']:
            self.add_player(player_name)

        player = self.stats['players'][player_name]

        # Обновляем общую статистику
        player['total_score'] += score
        player['games_played'] += 1

        if won:
            player['games_won'] += 1
        else:
            player['games_lost'] += 1

        if score > player['best_score']:
            player['best_score'] = score

        # Обновляем статистику по сложности
        if difficulty in player['difficulty_stats']:
            player['difficulty_stats'][difficulty]['played'] += 1
            if won:
                player['difficulty_stats'][difficulty]['won'] += 1

        # Добавляем в историю
        game_record = {
            'date': datetime.now().isoformat(),
            'difficulty': difficulty,
            'won': won,
            'score': score,
            'word': word
        }
        player['history'].append(game_record)

        # Оставляем только последние 100 игр в истории
        if len(player['history']) > 100:
            player['history'] = player['history'][-100:]

        self._save_stats()

    def get_player_stats(self, player_name: str) -> Dict | None:
        """Получить статистику игрока"""
        return self.stats['players'].get(player_name)

    def get_all_players(self) -> List[str]:
        """Получить список всех игроков"""
        return list(self.stats['players'].keys())

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """
        Получить таблицу лидеров

        Args:
            limit: Количество игроков в таблице

        Returns:
            Список словарей с информацией об игроках, отсортированных по общему счёту
        """
        leaderboard = []

        for name, stats in self.stats['players'].items():
            leaderboard.append({
                'name': name,
                'total_score': stats['total_score'],
                'games_played': stats['games_played'],
                'games_won': stats['games_won'],
                'best_score': stats['best_score'],
                'win_rate': round(stats['games_won'] / stats['games_played'] * 100, 1) if stats['games_played'] > 0 else 0
            })

        # Сортируем по общему счёту
        leaderboard.sort(key=lambda x: x['total_score'], reverse=True)

        return leaderboard[:limit]

    def get_player_history(self, player_name: str, limit: int = 10) -> List[Dict]:
        """
        Получить историю игр игрока

        Args:
            player_name: Имя игрока
            limit: Количество последних игр

        Returns:
            Список последних игр
        """
        player = self.stats['players'].get(player_name)
        if not player:
            return []

        history = player['history'][-limit:]
        history.reverse()  # Показываем от новых к старым
        return history

    def delete_player(self, player_name: str):
        """Удалить игрока из статистики"""
        if player_name in self.stats['players']:
            del self.stats['players'][player_name]
            self._save_stats()

    def reset_player_stats(self, player_name: str):
        """Сбросить статистику игрока"""
        if player_name in self.stats['players']:
            del self.stats['players'][player_name]
            self.add_player(player_name)

    def export_stats(self, filename: str):
        """Экспортировать всю статистику в отдельный файл"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
            return True
        except IOError:
            return False

    def import_stats(self, filename: str) -> Dict[str, List[str]]:
        """
        Импортировать статистику из файла

        Игроки, которые уже есть, и записи с ошибками пропускаются

        Returns:
            {'imported': [имена], 'existing': [имена], 'invalid': ['«имя»: причина', ...]}

        Raises:
            StatsImportError: файл не прочитан или не в формате статистики
        """
        try:
            # utf-8-sig читает и файлы с BOM (Блокнот Windows)
            with open(filename, 'r', encoding='utf-8-sig') as f:
                imported_stats = json.load(f)
        except FileNotFoundError:
            raise StatsImportError(f"файл {filename} не найден")
        except UnicodeDecodeError:
            raise StatsImportError("файл не в кодировке UTF-8")
        except json.JSONDecodeError as e:
            raise StatsImportError(f"файл не в формате JSON (строка {e.lineno}, столбец {e.colno})")
        except OSError as e:
            raise StatsImportError(f"не удалось прочитать файл: {e.strerror or e}")

        if not isinstance(imported_stats, dict) or not isinstance(imported_stats.get('players'), dict):
            raise StatsImportError('в файле нет списка игроков {"players": {...}}')

        result = {'imported': [], 'existing': [], 'invalid': []}

        # Объединяем статистику (если игрок уже существует, оставляем текущую)
        for player_name, player_data in imported_stats['players'].items():
            if player_name in self.stats['players']:
                result['existing'].append(player_name)
                continue

            error = self._validate_player(player_name, player_data)
            if error:
                result['invalid'].append(f"«{player_name}»: {error}")
            else:
                self.stats['players'][player_name] = player_data
                result['imported'].append(player_name)

        if result['imported']:
            self._save_stats()
        return result

    @staticmethod
    def _validate_player(player_name: str, player_data) -> str | None:
        """Проверить запись игрока из импортируемого файла; вернуть описание ошибки или None"""
        if not player_name.strip():
            return "пустое имя игрока"
        if not isinstance(player_data, dict):
            return "запись игрока - не объект"

        for key in COUNTERS:
            if not _is_count(player_data.get(key)):
                return f"поле {key} - не целое неотрицательное число"

        difficulty_stats = player_data.get('difficulty_stats')
        if not isinstance(difficulty_stats, dict) or not set(DIFFICULTIES) <= difficulty_stats.keys():
            return "в difficulty_stats нет всех уровней сложности"
        for difficulty, level in difficulty_stats.items():
            if not (isinstance(level, dict) and _is_count(level.get('played')) and _is_count(level.get('won'))):
                return f"неверная статистика уровня {difficulty}"

        history = player_data.get('history')
        if not isinstance(history, list):
            return "поле history - не список"
        for game in history:
            if not (isinstance(game, dict)
                    and isinstance(game.get('date'), str)
                    and isinstance(game.get('difficulty'), str)
                    and isinstance(game.get('won'), bool)
                    and _is_count(game.get('score'))
                    and isinstance(game.get('word'), str)):
                return "неверная запись в history"

        return None
