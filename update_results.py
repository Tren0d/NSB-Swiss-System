import csv
import pandas as pd


def update_match_result(round_num, team1, team2, score1, score2):
    """Обновляет результат конкретного боя в results.csv"""
    rows = []
    updated = False
    
    try:
        with open('results.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
        
        for row in rows:
            if (int(row['round']) == round_num and 
                row['team1'] == team1 and 
                row['team2'] == team2):
                row['score1'] = score1
                row['score2'] = score2
                updated = True
                print(f"✅ Обновлен результат: {team1} {score1} - {score2} {team2}")
        
        if updated:
            with open('results.csv', 'w', encoding='utf-8', newline='') as file:
                fieldnames = ['round', 'team1', 'team2', 'score1', 'score2', 'jury']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        else:
            print(f"❌ Бой не найден: раунд {round_num}, {team1} vs {team2}")
            
    except FileNotFoundError:
        print("❌ Файл results.csv не найден!")


def show_current_round():
    """Показывает результаты последнего раунда"""
    try:
        df = pd.read_csv('results.csv')
        last_round = df['round'].max()
        
        print(f"\n{'='*80}")
        print(f"РАУНД {last_round} - ТЕКУЩИЕ РЕЗУЛЬТАТЫ")
        print(f"{'='*80}")
        
        round_df = df[df['round'] == last_round]
        for _, row in round_df.iterrows():
            status = "✓" if row['score1'] != 0 or row['score2'] != 0 else "⏳"
            print(f"{status} {row['team1']:25} {row['score1']} - {row['score2']} {row['team2']:25} | {row['jury']}")
        
        print(f"{'='*80}\n")
        
    except FileNotFoundError:
        print("❌ Файл results.csv не найден!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


def show_standings():
    """Показывает турнирную таблицу"""
    try:
        df = pd.read_csv('results.csv')
        teams_scores = {}
        
        for _, row in df.iterrows():
            team1, team2 = row['team1'], row['team2']
            score1, score2 = row['score1'], row['score2']
            
            if team1 not in teams_scores:
                teams_scores[team1] = 0
            if team2 not in teams_scores:
                teams_scores[team2] = 0
            
            teams_scores[team1] += score1
            teams_scores[team2] += score2
        
        print(f"\n{'='*50}")
        print("ТУРНИРНАЯ ТАБЛИЦА")
        print(f"{'='*50}")
        
        sorted_teams = sorted(teams_scores.items(), key=lambda x: x[1], reverse=True)
        for i, (team, score) in enumerate(sorted_teams, 1):
            print(f"{i:2}. {team:30} {score:.2f}")
        
        print(f"{'='*50}\n")
        
    except FileNotFoundError:
        print("❌ Файл results.csv не найден!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


def interactive_update():
    """Интерактивное обновление результатов"""
    print("\n" + "="*60)
    print("ОБНОВЛЕНИЕ РЕЗУЛЬТАТОВ БОЕВ")
    print("="*60)
    
    show_current_round()
    
    print("Введите данные боя:")
    try:
        round_num = int(input("Номер раунда: "))
        team1 = input("Команда 1: ").strip()
        team2 = input("Команда 2: ").strip()
        score1 = float(input(f"Очки {team1}: "))
        score2 = float(input(f"Очки {team2}: "))
        
        update_match_result(round_num, team1, team2, score1, score2)
        
        print("\nОбновить еще один результат? (y/n)")
        if input().lower() == 'y':
            interactive_update()
        else:
            show_standings()
            
    except ValueError:
        print("❌ Ошибка ввода! Проверьте формат данных.")
    except KeyboardInterrupt:
        print("\n\nОтменено пользователем.")


def batch_update_from_text():
    """Пакетное обновление из текстового ввода"""
    print("\n" + "="*60)
    print("ПАКЕТНОЕ ОБНОВЛЕНИЕ")
    print("="*60)
    print("Введите результаты в формате:")
    print("Team1 vs Team2 --> score1 vs score2")
    print("Пустая строка для завершения\n")
    
    round_num = int(input("Номер раунда: "))
    
    while True:
        line = input().strip()
        if not line:
            break
        
        try:
            teams_part, scores_part = line.split(' --> ')
            team1, team2 = [t.strip() for t in teams_part.split(' vs ')]
            score1, score2 = [float(s.strip()) for s in scores_part.split(' vs ')]
            
            update_match_result(round_num, team1, team2, score1, score2)
            
        except ValueError:
            print(f"❌ Неверный формат: {line}")
    
    show_standings()


if __name__ == "__main__":
    print("\nВыберите действие:")
    print("1. Показать текущий раунд")
    print("2. Показать турнирную таблицу")
    print("3. Обновить результат боя")
    print("4. Пакетное обновление результатов")
    print("0. Выход")
    
    choice = input("\nВаш выбор: ").strip()
    
    if choice == '1':
        show_current_round()
    elif choice == '2':
        show_standings()
    elif choice == '3':
        interactive_update()
    elif choice == '4':
        batch_update_from_text()
    elif choice == '0':
        print("До свидания!")
    else:
        print("❌ Неверный выбор!")
