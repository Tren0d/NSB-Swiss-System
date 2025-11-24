import csv
from random import shuffle, choice
from functools import total_ordering
from statistics import mode
from collections import defaultdict


@total_ordering
class Team:
    def __init__(self, name, score=0, school=""):
        self.name = name
        self.score = score
        self.school = school
        self.opponents = []

    def buhholtz_coefficient(self, k=0):
        return sum(sorted([score for _, score in self.opponents])[k:])
    
    def add_opponent(self, opponent, score=0):
        self.opponents.append((opponent, score))
        self.score += score
    
    def __str__(self):
        return self.name

    def __eq__(self, other):
        if self.score != other.score:
            return False
        k = 0
        while self.buhholtz_coefficient(k) == other.buhholtz_coefficient(k) and k < len(self.opponents):
            k += 1
        return self.buhholtz_coefficient(k) == other.buhholtz_coefficient(k)
    
    def __ge__(self, other):
        if self.score == other.score:
            k = 0
            while self.buhholtz_coefficient(k) == other.buhholtz_coefficient(k) and k < len(self.opponents):
                k += 1
            return self.buhholtz_coefficient(k) >= other.buhholtz_coefficient(k)
        return self.score >= other.score


class Jury:
    def __init__(self, name, forbidden_schools=None, forbidden_teams=None):
        self.name = name
        self.forbidden_schools = set(forbidden_schools or [])
        self.forbidden_teams = set(forbidden_teams or [])
        self.judged_teams = set()
        self.rounds_count = 0
    
    def can_judge(self, team1, team2):
        """Проверяет, может ли жюри судить этот бой"""
        if team1.name in self.judged_teams or team2.name in self.judged_teams:
            return False
        if team1.school in self.forbidden_schools or team2.school in self.forbidden_schools:
            return False
        if team1.name in self.forbidden_teams or team2.name in self.forbidden_teams:
            return False
        return True
    
    def assign_match(self, team1, team2):
        """Назначает жюри на бой"""
        self.judged_teams.add(team1.name)
        self.judged_teams.add(team2.name)
        self.rounds_count += 1


def load_teams_from_csv(filename='teams.csv'):
    """Загружает команды из CSV файла"""
    teams = {}
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                team_name = row['team_name']
                school = row.get('school', '')
                teams[team_name] = Team(team_name, school=school)
    except FileNotFoundError:
        print(f"Файл {filename} не найден. Создайте его по образцу.")
    return teams


def load_jury_from_csv(filename='jury.csv'):
    """Загружает жюри из CSV файла"""
    jury_list = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row['name']
                forbidden_schools = [s.strip() for s in row.get('forbidden_schools', '').split(';') if s.strip()]
                forbidden_teams = [t.strip() for t in row.get('forbidden_teams', '').split(';') if t.strip()]
                jury_list.append(Jury(name, forbidden_schools, forbidden_teams))
    except FileNotFoundError:
        print(f"Файл {filename} не найден. Создайте его по образцу.")
    return jury_list


def load_results_from_csv(teams, filename='results.csv'):
    """Загружает результаты предыдущих туров из CSV"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                team1_name = row['team1']
                team2_name = row['team2']
                score1 = float(row['score1'])
                score2 = float(row['score2'])
                
                if team1_name in teams and team2_name in teams:
                    teams[team1_name].add_opponent(team2_name, score1)
                    teams[team2_name].add_opponent(team1_name, score2)
    except FileNotFoundError:
        print(f"Файл {filename} не найден. Начинаем с нуля.")


def save_results_to_csv(pairs, filename='results.csv', append=True):
    """Сохраняет результаты в CSV файл"""
    mode_write = 'a' if append else 'w'
    file_exists = append
    
    with open(filename, mode_write, encoding='utf-8', newline='') as file:
        fieldnames = ['round', 'team1', 'team2', 'score1', 'score2', 'jury']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        if not file_exists or not append:
            writer.writeheader()
        
        for pair_info in pairs:
            writer.writerow(pair_info)


def generate_pairings(teams):
    """Генерирует все возможные паросочетания"""
    if not teams:
        yield []
        return

    a = teams[0]
    for i in range(1, len(teams)):
        b = teams[i]
        rest = teams[1:i] + teams[i+1:]
        for pairs in generate_pairings(rest):
            yield [(a, b)] + pairs


def pairing_score(pairs):
    """Оценивает качество паросочетания (меньше = лучше)"""
    return sum((a.score - b.score) ** 2 for a, b in pairs)


def set_pairings(teams):
    """Создает оптимальное паросочетание по швейцарской системе"""
    teams_copy = teams.copy()
    
    if len(teams_copy) % 2 == 1:
        jurors = Team("Jurors", mode([t.score for t in teams_copy]) if teams_copy else 0)
        teams_copy.append(jurors)

    best_score = float("inf")
    best_pairs = None

    shuffle(teams_copy)

    all_pairings = list(generate_pairings(teams_copy))
    print(f"Рассматриваем {len(all_pairings)} вариантов паросочетания...")

    for pairing in all_pairings:
        score = pairing_score(pairing)
        if score < best_score:
            best_score = score
            best_pairs = pairing

    return best_pairs


def assign_jury_to_matches(pairs, jury_list, round_num):
    """Распределяет жюри по боям с учетом ограничений"""
    matches_with_jury = []
    unassigned_matches = []
    
    # Создаем счетчик боев для текущего раунда
    current_round_matches = defaultdict(int)
    
    # Пытаемся назначить жюри на каждый бой
    for team1, team2 in pairs:
        assigned = False
        
        # Сортируем жюри по нагрузке В ТЕКУЩЕМ РАУНДЕ, затем по общей нагрузке
        available_jury = sorted(
            jury_list, 
            key=lambda j: (current_round_matches[j.name], j.rounds_count)
        )
        
        # Перебираем жюри в порядке приоритета
        for jury in available_jury:
            if jury.can_judge(team1, team2):
                jury.assign_match(team1, team2)
                current_round_matches[jury.name] += 1
                matches_with_jury.append({
                    'round': round_num,
                    'team1': team1.name,
                    'team2': team2.name,
                    'score1': 0,
                    'score2': 0,
                    'jury': jury.name
                })
                assigned = True
                break
        
        if not assigned:
            # Если не удалось назначить жюри, ищем жюри с минимальными нарушениями
            best_jury = None
            min_violations = float('inf')
            
            available_jury = sorted(
                jury_list, 
                key=lambda j: (current_round_matches[j.name], j.rounds_count)
            )
            
            for jury in available_jury:
                violations = 0
                if team1.name in jury.judged_teams or team2.name in jury.judged_teams:
                    violations += 1
                
                if violations < min_violations:
                    min_violations = violations
                    best_jury = jury
            
            if best_jury:
                best_jury.assign_match(team1, team2)
                current_round_matches[best_jury.name] += 1
                matches_with_jury.append({
                    'round': round_num,
                    'team1': team1.name,
                    'team2': team2.name,
                    'score1': 0,
                    'score2': 0,
                    'jury': f"{best_jury.name} (конфликт!)"
                })
                print(f"⚠️  Конфликт: {best_jury.name} уже судил одну из команд в бою {team1} vs {team2}")
            else:
                unassigned_matches.append((team1, team2))
    
    return matches_with_jury, unassigned_matches


def print_round_schedule(matches_with_jury, round_num):
    """Выводит расписание раунда"""
    print(f"\n{'='*60}")
    print(f"РАУНД {round_num}")
    print(f"{'='*60}")
    for match in matches_with_jury:
        print(f"{match['team1']:25} vs {match['team2']:25} | Жюри: {match['jury']}")
    print(f"{'='*60}\n")


def create_sample_files():
    """Создает примеры CSV файлов"""
    # Пример teams.csv
    with open('teams.csv', 'w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['team_name', 'school'])
        writer.writeheader()
        writer.writerow({'team_name': 'NEND', 'school': 'NIS Almaty'})
        writer.writerow({'team_name': 'MA^3', 'school': 'Miras'})
        writer.writerow({'team_name': 'Euler', 'school': 'BIL'})
    
    # Пример jury.csv
    with open('jury.csv', 'w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['name', 'forbidden_schools', 'forbidden_teams'])
        writer.writeheader()
        writer.writerow({'name': 'Иванов А.', 'forbidden_schools': 'NIS Almaty', 'forbidden_teams': ''})
        writer.writerow({'name': 'Петрова Б.', 'forbidden_schools': 'Miras;BIL', 'forbidden_teams': ''})
        writer.writerow({'name': 'Сидоров В.', 'forbidden_schools': '', 'forbidden_teams': 'Euler'})
    
    print("✅ Созданы примеры файлов teams.csv и jury.csv")


# ОСНОВНАЯ ПРОГРАММА
if __name__ == "__main__":
    print("Система парирования команд и распределения жюри")
    print("=" * 60)
    
    # Загружаем данные
    teams_dict = load_teams_from_csv('teams.csv')
    jury_list = load_jury_from_csv('jury.csv')
    
    if not teams_dict:
        print("⚠️  Команды не загружены. Создать примеры файлов? (y/n)")
        if input().lower() == 'y':
            create_sample_files()
        exit()
    
    # Загружаем результаты предыдущих туров
    load_results_from_csv(teams_dict, 'results.csv')
    
    # Подсчитываем текущий раунд
    current_round = 1
    if teams_dict:
        max_opponents = max(len(team.opponents) for team in teams_dict.values())
        current_round = max_opponents + 1
    
    # Создаем пары
    teams_list = list(teams_dict.values())
    pairs = set_pairings(teams_list)
    
    # Распределяем жюри
    if jury_list:
        matches_with_jury, unassigned = assign_jury_to_matches(pairs, jury_list, current_round)
        
        if unassigned:
            print(f"⚠️  Не удалось назначить жюри на {len(unassigned)} боев!")
            for team1, team2 in unassigned:
                print(f"   {team1} vs {team2}")
        
        # Выводим расписание
        print_round_schedule(matches_with_jury, current_round)
        
        # Сохраняем в CSV
        save_results_to_csv(matches_with_jury, 'results.csv', append=True)
        print("✅ Результаты сохранены в results.csv")
        
        # Статистика жюри
        print("\nСтатистика жюри (всего боев):")
        for jury in sorted(jury_list, key=lambda j: j.rounds_count, reverse=True):
            print(f"  {jury.name}: {jury.rounds_count} боев")
        
        # Статистика текущего раунда
        print(f"\nРаспределение в раунде {current_round}:")
        round_distribution = defaultdict(int)
        for match in matches_with_jury:
            jury_name = match['jury'].replace(" (конфликт!)", "")
            round_distribution[jury_name] += 1
        
        for jury_name, count in sorted(round_distribution.items(), key=lambda x: x[1], reverse=True):
            conflict_marker = " ⚠️" if "(конфликт!)" in str([m['jury'] for m in matches_with_jury if jury_name in m['jury']]) else ""
            print(f"  {jury_name}: {count} боев{conflict_marker}")
    else:
        print("⚠️  Жюри не загружены. Создаются пары без назначения жюри.")
        for team1, team2 in pairs:
            print(f"{team1.name}({team1.score}) vs {team2.name}({team2.score})")
