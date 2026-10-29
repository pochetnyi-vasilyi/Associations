"""
Главный файл игры "Ассоциации"
Консольный интерфейс для игры
"""
import os
import sys
from dictionary_parser import DictionaryParser, DEFAULT_DICTIONARY_PATH
from game_logic import AssociationsGame, Difficulty
from player_stats import PlayerStats


class AssociationsGameUI:
    """Пользовательский интерфейс игры"""

    def __init__(self):
        self.dictionary_path = DEFAULT_DICTIONARY_PATH
        self.parser = None
        self.game = None
        self.stats = PlayerStats()
        self.current_player = None

    def clear_screen(self):
        """Очистить экран консоли"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """Вывести заголовок игры"""
        print("=" * 60)
        print("           ИГРА 'АССОЦИАЦИИ'")
        print("=" * 60)
        print()

    def load_dictionary(self):
        """Загрузить словарь"""
        print("Загрузка ассоциативного словаря...")
        try:
            self.parser = DictionaryParser(self.dictionary_path)
            dictionary = self.parser.parse()

            if not dictionary:
                print("Ошибка: Словарь пуст или не удалось его загрузить!")
                return False

            print(f"Словарь загружен! Доступно слов: {self.parser.get_word_count()}")
            self.game = AssociationsGame(dictionary)
            return True

        except FileNotFoundError:
            print(f"Ошибка: Файл словаря не найден по пути: {self.dictionary_path}")
            return False
        except Exception as e:
            print(f"Ошибка при загрузке словаря: {e}")
            return False

    def select_player(self):
        """Выбрать или создать игрока"""
        self.clear_screen()
        self.print_header()

        players = self.stats.get_all_players()

        if players:
            print("Существующие игроки:")
            for i, player in enumerate(players, 1):
                stats = self.stats.get_player_stats(player)
                print(f"{i}. {player} - Игр: {stats['games_played']}, Очков: {stats['total_score']}")
            print()

        print("Введите номер игрока или имя нового игрока:")
        choice = input("> ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(players):
            self.current_player = players[int(choice) - 1]
        elif choice and not choice.isdigit():
            self.current_player = choice
            self.stats.add_player(self.current_player)
        else:
            print("Некорректный ввод!")
            input("Нажмите Enter для продолжения...")
            return self.select_player()

        print(f"\nПривет, {self.current_player}!")

    def select_difficulty(self) -> Difficulty:
        """Выбрать уровень сложности"""
        print("\nВыберите уровень сложности:")
        print("1. Легкий (5 ассоциаций, 5 попыток)")
        print("2. Средний (4 ассоциации, 4 попытки)")
        print("3. Сложный (3 ассоциации, 3 попытки)")
        print("4. Эксперт (2 ассоциации, 2 попытки)")

        while True:
            choice = input("\n> ").strip()
            if choice == '1':
                return Difficulty.EASY
            elif choice == '2':
                return Difficulty.MEDIUM
            elif choice == '3':
                return Difficulty.HARD
            elif choice == '4':
                return Difficulty.EXPERT
            else:
                print("Некорректный выбор! Введите число от 1 до 4.")

    def play_round(self, difficulty: Difficulty):
        """Играть один раунд"""
        self.clear_screen()
        self.print_header()

        print(f"Уровень: {difficulty.name}")
        print()

        # Начинаем новый раунд
        if not self.game.start_new_round(difficulty):
            print("Ошибка: Не удалось найти подходящее слово!")
            input("\nНажмите Enter для продолжения...")
            return

        # Открываем первую ассоциацию
        self.game.reveal_next_association()

        game_won = False
        round_score = 0

        while not self.game.is_game_over():
            self.clear_screen()
            self.print_header()

            print(f"Игрок: {self.current_player}")
            print(f"Уровень: {difficulty.name}")
            print(f"Попыток осталось: {self.game.attempts_left}")
            print()

            # Показываем открытые ассоциации
            print("Ассоциации:")
            for i, (assoc, freq) in enumerate(self.game.shown_associations, 1):
                print(f"  {i}. {assoc} (частота: {freq})")
            print()

            # Меню действий
            print("Что делать?")
            print("1. Попытаться угадать слово")
            print("2. Открыть следующую ассоциацию")
            print("3. Взять подсказку (-100 очков)")
            print("4. Сдаться")

            action = input("\n> ").strip()

            if action == '1':
                # Попытка угадать
                guess = input("\nВаш ответ: ").strip()
                correct, points = self.game.make_guess(guess)

                if correct:
                    game_won = True
                    round_score = points
                    self.clear_screen()
                    self.print_header()
                    print("*** ПРАВИЛЬНО! ***")
                    print(f"\nСлово было: {self.game.get_current_word()}")
                    print(f"Вы получили {points} очков!")
                    input("\nНажмите Enter для продолжения...")
                    break
                else:
                    print(f"\nНеправильно! Попробуйте ещё раз.")
                    if not self.game.is_game_over():
                        # Автоматически открываем следующую ассоциацию
                        next_assoc = self.game.reveal_next_association()
                        if next_assoc:
                            print(f"Открыта новая ассоциация: {next_assoc[0]}")
                    input("\nНажмите Enter для продолжения...")

            elif action == '2':
                # Открыть следующую ассоциацию
                next_assoc = self.game.reveal_next_association()
                if next_assoc:
                    print(f"\nОткрыта новая ассоциация: {next_assoc[0]} (частота: {next_assoc[1]})")
                else:
                    print("\nВсе ассоциации уже открыты!")
                input("\nНажмите Enter для продолжения...")

            elif action == '3':
                # Взять подсказку
                hint = self.game.get_hint()
                if hint:
                    print(f"\nПодсказка: {hint}")
                    print("(Вы потеряли 100 очков)")
                input("\nНажмите Enter для продолжения...")

            elif action == '4':
                # Сдаться
                self.clear_screen()
                self.print_header()
                print("Вы сдались!")
                print(f"Загаданное слово было: {self.game.get_current_word()}")
                input("\nНажмите Enter для продолжения...")
                break

        # Если игра закончилась без угадывания
        if not game_won and self.game.is_game_over():
            self.clear_screen()
            self.print_header()
            print("Попытки закончились!")
            print(f"Загаданное слово было: {self.game.get_current_word()}")
            input("\nНажмите Enter для продолжения...")

        # Записываем результат
        self.stats.record_game(
            self.current_player,
            difficulty.name,
            game_won,
            round_score,
            self.game.get_current_word()
        )

    def show_stats(self):
        """Показать статистику"""
        self.clear_screen()
        self.print_header()

        print(f"Статистика игрока: {self.current_player}")
        print("=" * 60)

        player_stats = self.stats.get_player_stats(self.current_player)

        if not player_stats:
            print("Статистика отсутствует")
            input("\nНажмите Enter для продолжения...")
            return

        print(f"\nОбщий счёт: {player_stats['total_score']}")
        print(f"Игр сыграно: {player_stats['games_played']}")
        print(f"Побед: {player_stats['games_won']}")
        print(f"Поражений: {player_stats['games_lost']}")
        print(f"Лучший результат: {player_stats['best_score']}")

        if player_stats['games_played'] > 0:
            win_rate = player_stats['games_won'] / player_stats['games_played'] * 100
            print(f"Процент побед: {win_rate:.1f}%")

        print("\nСтатистика по уровням сложности:")
        for difficulty, diff_stats in player_stats['difficulty_stats'].items():
            if diff_stats['played'] > 0:
                win_rate = diff_stats['won'] / diff_stats['played'] * 100
                print(f"  {difficulty}: {diff_stats['played']} игр, {diff_stats['won']} побед ({win_rate:.1f}%)")

        print("\nПоследние игры:")
        history = self.stats.get_player_history(self.current_player, 5)
        for i, game in enumerate(history, 1):
            result = "+" if game['won'] else "-"
            print(f"  {i}. [{result}] {game['difficulty']} - {game['word']} ({game['score']} очков)")

        input("\nНажмите Enter для продолжения...")

    def show_leaderboard(self):
        """Показать таблицу лидеров"""
        self.clear_screen()
        self.print_header()

        print("ТАБЛИЦА ЛИДЕРОВ")
        print("=" * 60)

        leaderboard = self.stats.get_leaderboard(10)

        if not leaderboard:
            print("Таблица лидеров пуста")
        else:
            print(f"\n{'#':<4} {'Игрок':<20} {'Очки':<10} {'Игр':<8} {'Побед':<8} {'%':<6}")
            print("-" * 60)
            for i, player in enumerate(leaderboard, 1):
                print(f"{i:<4} {player['name']:<20} {player['total_score']:<10} "
                      f"{player['games_played']:<8} {player['games_won']:<8} {player['win_rate']:<6.1f}")

        input("\nНажмите Enter для продолжения...")

    def main_menu(self):
        """Главное меню"""
        while True:
            self.clear_screen()
            self.print_header()

            print(f"Игрок: {self.current_player}")
            player_stats = self.stats.get_player_stats(self.current_player)
            if player_stats:
                print(f"Общий счёт: {player_stats['total_score']}")
            print()

            print("ГЛАВНОЕ МЕНЮ:")
            print("1. Играть")
            print("2. Моя статистика")
            print("3. Таблица лидеров")
            print("4. Сменить игрока")
            print("5. Выход")

            choice = input("\n> ").strip()

            if choice == '1':
                difficulty = self.select_difficulty()
                self.play_round(difficulty)
            elif choice == '2':
                self.show_stats()
            elif choice == '3':
                self.show_leaderboard()
            elif choice == '4':
                self.select_player()
            elif choice == '5':
                print("\nСпасибо за игру! До встречи!")
                sys.exit(0)
            else:
                print("Некорректный выбор!")
                input("\nНажмите Enter для продолжения...")

    def run(self):
        """Запустить игру"""
        self.clear_screen()
        self.print_header()

        # Загружаем словарь
        if not self.load_dictionary():
            input("\nНажмите Enter для выхода...")
            sys.exit(1)

        input("\nНажмите Enter для продолжения...")

        # Выбираем игрока
        self.select_player()
        input("\nНажмите Enter для начала игры...")

        # Главное меню
        self.main_menu()


if __name__ == '__main__':
    game_ui = AssociationsGameUI()
    game_ui.run()
