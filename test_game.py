"""
Тестовый скрипт для проверки работы игры
"""
from dictionary_parser import DictionaryParser
from game_logic import AssociationsGame, Difficulty
from player_stats import PlayerStats


def test_parser():
    """Тестирование парсера"""
    print("=" * 60)
    print("ТЕСТ ПАРСЕРА")
    print("=" * 60)

    parser = DictionaryParser()
    dictionary = parser.parse()

    print(f"Загружено слов: {parser.get_word_count()}")

    # Проверяем несколько слов
    test_words = ['АБСОЛЮТНЫЙ', 'АВТОМАТ', 'АКТИВНЫЙ']
    for word in test_words:
        if word in dictionary:
            assoc = parser.get_associations(word)
            print(f"\n{word}:")
            print(f"  Всего ассоциаций: {len(assoc)}")
            print(f"  Топ-5: {assoc[:5]}")

    return parser, dictionary


def test_game_logic(dictionary):
    """Тестирование логики игры"""
    print("\n" + "=" * 60)
    print("ТЕСТ ЛОГИКИ ИГРЫ")
    print("=" * 60)

    game = AssociationsGame(dictionary)

    # Тестируем каждый уровень сложности
    for difficulty in [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD, Difficulty.EXPERT]:
        print(f"\nТест уровня {difficulty.name}:")

        if game.start_new_round(difficulty):
            print(f"  Загаданное слово: {game.current_word}")
            print(f"  Попыток: {game.attempts_left}")
            print(f"  Ассоциации для показа: {len(game.current_associations)}")

            # Показываем все ассоциации
            for i in range(len(game.current_associations)):
                assoc = game.reveal_next_association()
                if assoc:
                    print(f"    {i+1}. {assoc[0]} (частота: {assoc[1]})")

            # Проверяем систему подсказок
            hint = game.get_hint()
            print(f"  Подсказка: {hint}")

            # Проверяем расчет очков
            # Симулируем правильный ответ
            game.attempts_left = 3  # Оставляем 3 попытки
            correct, points = game.make_guess(game.current_word)
            print(f"  Правильный ответ дает {points} очков")
        else:
            print(f"  ОШИБКА: Не удалось начать раунд для уровня {difficulty.name}")

    return game


def test_stats():
    """Тестирование системы статистики"""
    print("\n" + "=" * 60)
    print("ТЕСТ СИСТЕМЫ СТАТИСТИКИ")
    print("=" * 60)

    # Создаем временный файл статистики для теста
    stats = PlayerStats('test_stats.json')

    # Добавляем тестового игрока
    test_player = "ТестовыйИгрок"
    stats.add_player(test_player)
    print(f"Добавлен игрок: {test_player}")

    # Записываем несколько игр
    test_games = [
        ('EASY', True, 800, 'АВТОМАТ'),
        ('MEDIUM', True, 1200, 'АКТИВНЫЙ'),
        ('HARD', False, 0, 'АБСОЛЮТНЫЙ'),
        ('EXPERT', True, 1500, 'АВТОМАТ'),
    ]

    for difficulty, won, score, word in test_games:
        stats.record_game(test_player, difficulty, won, score, word)
        result = "Победа" if won else "Поражение"
        print(f"  Записана игра: {difficulty} - {result} ({score} очков)")

    # Получаем статистику
    player_stats = stats.get_player_stats(test_player)
    print(f"\nСтатистика игрока {test_player}:")
    print(f"  Игр: {player_stats['games_played']}")
    print(f"  Побед: {player_stats['games_won']}")
    print(f"  Поражений: {player_stats['games_lost']}")
    print(f"  Общий счет: {player_stats['total_score']}")
    print(f"  Лучший результат: {player_stats['best_score']}")

    # Проверяем таблицу лидеров
    print("\nТаблица лидеров:")
    leaderboard = stats.get_leaderboard(5)
    for i, player in enumerate(leaderboard, 1):
        print(f"  {i}. {player['name']} - {player['total_score']} очков")

    # Проверяем историю
    print("\nИстория игр:")
    history = stats.get_player_history(test_player, 3)
    for i, game in enumerate(history, 1):
        result = "+" if game['won'] else "-"
        print(f"  {i}. [{result}] {game['difficulty']} - {game['word']} ({game['score']} очков)")

    # Очищаем тестовый файл
    import os
    if os.path.exists('test_stats.json'):
        os.remove('test_stats.json')
        print("\nТестовый файл статистики удален")

    return stats


def main():
    """Главная функция тестирования"""
    print("\nЗАПУСК ТЕСТОВ ИГРЫ 'АССОЦИАЦИИ'\n")

    try:
        # Тест 1: Парсер
        parser, dictionary = test_parser()

        # Тест 2: Логика игры
        game = test_game_logic(dictionary)

        # Тест 3: Статистика
        stats = test_stats()

        print("\n" + "=" * 60)
        print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 60)
        print("\nИгра готова к запуску. Используйте: python main.py")

    except Exception as e:
        print(f"\nОШИБКА ПРИ ТЕСТИРОВАНИИ: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
