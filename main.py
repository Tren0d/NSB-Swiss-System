from random import shuffle
from functools import total_ordering
from statistics import mode
from itertools import permutations


@total_ordering
class Team:
    def __init__(self, name, score=0):
        self.name = name
        self.score = score
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

def have_played_before(team1, team2):
    return any([opponent == team2.name for opponent, _ in team1.opponents])

def generate_pairings(teams):
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
    return sum((a.score - b.score) ** 2 for a, b in pairs)

def set_pairings(teams):
    if len(teams) % 2 == 1:
        jurors = Team("Jurors", mode([t.score for t in teams]))
        teams.append(jurors)

    best_score = float("inf")
    best_pairs = None

    shuffle(teams)

    x = list(generate_pairings(teams))

    print(len(x))

    for pairing in x:
        score = pairing_score(pairing)
        if score < best_score:
            best_score = score
            best_pairs = pairing

    return best_pairs

names = ["A", "B", "C", "D"]

team_names = []
teams = []

with open('pairings.txt') as file:
    for s in file.read().split('\n'):
        if s == '':
            continue
        [teams_s, scores_s] = s.split(" --> ")
        team = teams_s.split(" vs ")
        score = list(map(float, scores_s.split(" vs ")))
        for i in range(2):
            if team[i] not in team_names:
                team_names.append(team[i])
                teams.append(Team(team[i]))
            for j in teams:
                if j.name == team[i]:
                    j.add_opponent(team[1-i], score[i])

pairs = []

if len(teams) == 0:
    for i in range(0,len(names),2):
        pairs.append((Team(names[i]), Team(names[i+1])))
else:
    pairs = set_pairings(teams)

#for i in teams: print(f"{i.name}: {i.score}, {i.opponents}")
                             
with open('pairings.txt', 'a') as file:
    for (team1, team2) in pairs:
        file.write(f"{team1} vs {team2} --> 0 vs 0\n")
        print(f"{team1}({team1.score}) vs {team2}({team2.score})")
    file.write("\n")
