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


def have_played_before(team1, team2):
    """Проверяет, играли ли команды друг с другом ранее"""
    return any(opponent == team2.name for opponent, _ in team1.opponents)


def pairing_score(pairs):
    """Оценивает качество паросочетания (меньше = лучше)"""
    score = 0
    for a, b in pairs:
        # Штраф за разницу в очках (чем меньше, тем лучше)
        score += (a.score - b.score) ** 2
        # Большой штраф, если команды уже играли друг с другом
        if have_played_before(a, b):
            score += 1000
    return score


def limited_pairing(teams):
    """Генерирует ограниченное количество случайных паросочетаний"""
    teams_copy = teams.copy()
    
    shuffle(teams_copy)
    pairs = []
    
    for i in range(0, len(teams_copy), 2):
        if i + 1 < len(teams_copy):
            pairs.append((teams_copy[i], teams_copy[i+1]))
    
    return pairs


def greedy_pairing(teams):
    """Жадный алгоритм парирования - быстрый для небольшого числа команд"""
    teams_sorted = sorted(teams, key=lambda t: t.score, reverse=True)
    pairs = []
    used = set()
    
    for i, team1 in enumerate(teams_sorted):
        if team1.name in used:
            continue
        
        best_opponent = None
        best_score_diff = float('inf')
        
        # Ищем лучшего оппонента среди оставшихся команд
        for team2 in teams_sorted[i+1:]:
            if team2.name in used:
                continue
            
            # Оцениваем качество пары
            score_diff = abs(team1.score - team2.score)
            played_before = have_played_before(team1, team2)
            
            # Если команды уже играли, добавляем большой штраф
            if played_before:
                score_diff += 1000
            
            if score_diff < best_score_diff:
                best_score_diff = score_diff
                best_opponent = team2
        
        if best_opponent:
            pairs.append((team1, best_opponent))
            used.add(team1.name)
            used.add(best_opponent.name)
    
    return pairs


def set_pairings(teams):
    """Создает оптимальное паросочетание по швейцарской системе"""
    teams_copy = teams.copy()
    
    if len(teams_copy) % 2 == 1:
        jurors = Team("Jurors", mode([t.score for t in teams_copy]) if teams_copy else 0)
        teams_copy.append(jurors)

    teams_sorted = sorted(teams, key=lambda t: t.score, reverse=True)
    best_possible_score = 0
    for i in range(0,len(teams),2):
        best_possible_score += (teams_sorted[i].score - teams_sorted[i+1].score) ** 2
    best_score = 100000000
    best_pairs = None
    times = 0

    while best_score > best_possible_score and times < 1000000:
        pairing = limited_pairing(teams)
        score = pairing_score(pairing)
        if score < best_score:
            best_score = score
            best_pairs = pairing
            print(best_score)
        times += 1
        
    print(f"Лучший счет паросочетания: {best_score}")
    return best_pairs


def assign_jury_to_matches(pairs, jury_list, round_num):
    """Распределяет жюри по боям с учетом ограничений"""
    matches_with_jury = []
    unassigned_matches = []
    shuffle(jury_list)
    
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


def print_pairing_quality(pairs):
    """Выводит информацию о качестве паросочетания"""
    print("\n📊 Качество паросочетания:")
    
    total_diff = 0
    replays = 0
    
    for team1, team2 in pairs:
        diff = (team1.score - team2.score) ** 2
        total_diff += diff
        
        if have_played_before(team1, team2):
            replays += 1
            print(f"  ⚠️  {team1.name} vs {team2.name} - ПОВТОР! (разница: {diff:.2f})")
        elif diff > 1.0:
            print(f"  ⚡ {team1.name} ({team1.score:.1f}) vs {team2.name} ({team2.score:.1f}) - разница: {diff:.2f}")
    
    print(f"\n  Разница в очках: {total_diff:.3f}")
    print(f"  Повторных встреч: {replays}")
    
    if replays > 0:
        print("  ⚠️  Есть повторные встречи")
    
    print()


def print_round_schedule(matches_with_jury, round_num, teams_dict):
    """Выводит расписание раунда"""
    print(f"\n{'='*80}")
    print(f"РАУНД {round_num}")
    print(f"{'='*80}")
    
    for match in matches_with_jury:
        team1_name = match['team1']
        team2_name = match['team2']
        jury = match['jury']
        
        # Получаем очки команд
        team1_score = teams_dict.get(team1_name).score if team1_name in teams_dict else 0
        team2_score = teams_dict.get(team2_name).score if team2_name in teams_dict else 0
        
        print(f"{team1_name:27} ({team1_score:.2f}) vs {team2_name:27} ({team2_score:.2f}) | {jury}")
    
    print(f"{'='*80}\n")


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
    
    # Показываем качество паросочетания
    print_pairing_quality(pairs)
    
    # Распределяем жюри
    if jury_list:
        matches_with_jury, unassigned = assign_jury_to_matches(pairs, jury_list, current_round)
        
        if unassigned:
            print(f"⚠️  Не удалось назначить жюри на {len(unassigned)} боев!")
            for team1, team2 in unassigned:
                print(f"   {team1} vs {team2}")
        
        # Выводим расписание
        print_round_schedule(matches_with_jury, current_round, teams_dict)
        
        # Сохраняем в CSV
        save_results_to_csv(matches_with_jury, 'results.csv', append=True)
        print("✅ Результаты сохранены в results.csv")
    else:
        print("⚠️  Жюри не загружены. Создаются пары без назначения жюри.")
        for team1, team2 in pairs:
            print(f"{team1.name}({team1.score}) vs {team2.name}({team2.score})")
