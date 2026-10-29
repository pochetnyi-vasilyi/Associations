"""
Тестовый скрипт для проверки работы игры
"""
import json
import os
import re
import sys
import tempfile
from dictionary_parser import DictionaryParser
from game_logic import AssociationsGame, Difficulty, GameConfig
from player_stats import PlayerStats, StatsImportError


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

    assert parser.get_word_count() == 1000, "в словаре 1000 стимулов"
    assert all(re.fullmatch(r'[А-ЯЁ \-]+', word) for word in dictionary), "стимулы - слова заглавными буквами"
    # Число разных реакций - из итоговых строк статей (538+201+18+135, 546+124+3+75)
    assert len(dictionary['АБСОЛЮТНЫЙ']) == 201
    assert len(dictionary['АВТОМАТ']) == 124
    assert dictionary['АВТОМАТ'][0] == ('Калашникова', 152)
    assert ('по-любому', 1) in dictionary['АБСОЛЮТНЫЙ'], "перенос строки после дефиса"
    assert ('черный, стреляет', 1) in dictionary['АВТОМАТ'], "{,} - запятая внутри ассоциации"
    assert ('Россия', 7) in dictionary['РУССКИЙ'], "статья РУССКИЙ не пропущена"
    assert ('Россия', 7) not in dictionary['РУКИ'], "реакции РУССКИЙ не попали в РУКИ"

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
        config = GameConfig.get_config(difficulty)

        assert game.start_new_round(difficulty), f"не удалось начать раунд для уровня {difficulty.name}"
        print(f"  Загаданное слово: {game.current_word}")
        print(f"  Попыток: {game.attempts_left}")
        print(f"  Ассоциации для показа: {len(game.current_associations)}")

        # Показываем все ассоциации
        for i in range(len(game.current_associations)):
            assoc = game.reveal_next_association()
            if assoc:
                print(f"    {i+1}. {assoc[0]} (частота: {assoc[1]})")

        frequencies = [freq for _, freq in game.shown_associations]
        assert len(frequencies) == config['associations_count']
        assert all(freq >= config['min_frequency'] for freq in frequencies)
        assert frequencies == sorted(frequencies), "ассоциации открываются от редких к частым"

        # Проверяем систему подсказок
        hint = game.get_hint()
        print(f"  Подсказка: {hint}")
        assert hint == game.current_word[:1] + '...'

        # Проверяем расчет очков: первая попытка, одна подсказка
        correct, points = game.make_guess(game.current_word.lower())
        print(f"  Правильный ответ с первой попытки дает {points} очков")
        assert correct
        assert points == config['attempts'] * config['multiplier'] * 100 + 500 - 100

        # Победа с последней попытки тоже дает очки
        game.start_new_round(difficulty)
        for _ in range(config['attempts'] - 1):
            game.make_guess('неверный ответ')
        correct, points = game.make_guess(game.current_word)
        print(f"  Правильный ответ с последней попытки дает {points} очков")
        assert correct and points == config['multiplier'] * 100

    return game


def test_stats():
    """Тестирование системы статистики"""
    print("\n" + "=" * 60)
    print("ТЕСТ СИСТЕМЫ СТАТИСТИКИ")
    print("=" * 60)

    # Создаем временный файл статистики для теста (остаток прошлого запуска удаляем)
    if os.path.exists('test_stats.json'):
        os.remove('test_stats.json')
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

    assert player_stats['games_played'] == 4
    assert player_stats['games_won'] == 3 and player_stats['games_lost'] == 1
    assert player_stats['total_score'] == 3500 and player_stats['best_score'] == 1500
    assert player_stats['difficulty_stats']['HARD'] == {'played': 1, 'won': 0}
    assert leaderboard[0]['name'] == test_player and leaderboard[0]['win_rate'] == 75.0
    assert [game['word'] for game in history] == ['АВТОМАТ', 'АБСОЛЮТНЫЙ', 'АКТИВНЫЙ'], "история от новых к старым"

    # Очищаем тестовый файл
    if os.path.exists('test_stats.json'):
        os.remove('test_stats.json')
        print("\nТестовый файл статистики удален")

    return stats


def test_import():
    """Тестирование импорта статистики"""
    print("\n" + "=" * 60)
    print("ТЕСТ ИМПОРТА СТАТИСТИКИ")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmp:
        # Файл для импорта: два корректных игрока и два с ошибками в данных
        source = PlayerStats(os.path.join(tmp, 'source.json'))
        for name in ('Иван', 'Пётр', 'Сломанный', 'БезИстории'):
            source.record_game(name, 'EASY', True, 1000, 'АВТОМАТ')
        source.stats['players']['Сломанный']['games_played'] = '5'
        source.stats['players']['БезИстории']['history'] = None
        assert source.export_stats(os.path.join(tmp, 'import.json'))

        stats_file = os.path.join(tmp, 'stats.json')
        stats = PlayerStats(stats_file)
        stats.add_player('Иван')
        result = stats.import_stats(os.path.join(tmp, 'import.json'))
        print(f"Результат импорта: {result}")

        assert result['imported'] == ['Пётр']
        assert result['existing'] == ['Иван']
        assert [error.split(':')[0] for error in result['invalid']] == ['«Сломанный»', '«БезИстории»']
        assert 'Сломанный' not in stats.get_all_players()
        assert PlayerStats(stats_file).get_player_stats('Пётр')['total_score'] == 1000, "импорт сохранен в файл"
        stats.get_leaderboard()

        # Файлы, которые нельзя импортировать
        bad_files = {
            'missing.json': None,
            'broken.json': b'{"players": ',
            'cp1251.json': '{"players": {"Иван": {}}}'.encode('cp1251'),
            'list.json': b'[]',
            'players_list.json': b'{"players": []}',
        }
        for name, content in bad_files.items():
            path = os.path.join(tmp, name)
            if content is not None:
                with open(path, 'wb') as f:
                    f.write(content)
            try:
                stats.import_stats(path)
            except StatsImportError as e:
                print(f"  {name}: {e}")
            else:
                raise AssertionError(f"{name} импортирован без ошибки")

        try:
            stats.import_stats(tmp)
        except StatsImportError as e:
            print(f"  папка вместо файла: {e}")
        else:
            raise AssertionError("папка импортирована без ошибки")

        # Файл с BOM (Блокнот Windows) импортируется
        bom_file = os.path.join(tmp, 'bom.json')
        with open(bom_file, 'w', encoding='utf-8-sig') as f:
            json.dump({'players': {'Анна': source.get_player_stats('Пётр')}}, f, ensure_ascii=False)
        assert stats.import_stats(bom_file)['imported'] == ['Анна']


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

        # Тест 4: Импорт статистики
        test_import()

        print("\n" + "=" * 60)
        print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 60)
        print("\nИгра готова к запуску. Используйте: python main.py")

    except Exception as e:
        print(f"\nОШИБКА ПРИ ТЕСТИРОВАНИИ: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
