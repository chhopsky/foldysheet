import json
import argparse
import sys
import logging
import config
import dateutil.parser
from whatif import whatifoutcomes

def tiebreaker(possibility):
    possibility["standings"]["needs_tiebreaker"] = set()
    possibility["standings"]["tiebreaker_teams"] = set()
    for tie_position in possibility["standings"]["tied_for"]:
        
        tie_count = possibility["standings"]["tie"][str(tie_position)]
        cutoff = config.PLAYOFFS_CUTOFF_POSITION
        if tie_position <= cutoff < tie_position + tie_count - 1:
            possibility["standings"]["tie_broken"] = {tie_position: False}
            tied_teams = {}
            tie_data = { "complete": True, "sov": []}
            for key, value in possibility["standings"].items():
                if value == tie_position:
                    tied_teams[key] = { "wins": 0 }

            for match in previous_matches:
                if match["status"] == "finished":
                    winner = match["winner"]["acronym"]
                    team1 = match["opponents"][0]["opponent"]["acronym"]
                    team2 = match["opponents"][1]["opponent"]["acronym"]

                    if team1 in tied_teams.keys() and team2 in tied_teams.keys():
                        tied_teams[winner]["wins"] += 1
                        match_start = dateutil.parser.isoparse(match["begin_at"])
                        match_end = dateutil.parser.isoparse(match["end_at"])
                        match_time = match_end - match_start
                        tie_data["sov"].append((winner, match_time.seconds))
            
            for unfinished_match in possibility["matches"]:
                team1 = unfinished_match["opponents"][0]
                team2 = unfinished_match["opponents"][1]
                if team1 in tied_teams.keys() and team2 in tied_teams.keys():
                    winner = unfinished_match["winner"]
                    tied_teams[winner]["wins"] += 1
                    tie_data["complete"] = False

            pass

            if tie_count == 2:
                # check played matches

                for team, score in tied_teams.items():
                    if score["wins"] == 0:
                        possibility["standings"][team] += 1
                        possibility["standings"]["tie_broken"][tie_position] = True
                    if score["wins"] == 1 and tie_data["complete"] == True:
                        tie_data["sov"].sort(key=lambda a: a[1])
                        if tie_data["sov"][0][0] != team:
                            possibility["standings"][team] += 1
                            possibility["standings"]["tie_broken"][tie_position] = True
                    possibility["standings"]["needs_tiebreaker"].add(tie_position)
                    possibility["standings"]["tiebreaker_teams"].add(team)
                pass
                            
            elif tie_count == 3:
                # do three-way res. if only one part of the tie resolves, create a new tie
                # scenarios:
                # all teams 2-2 (dont resolve)
                # 3-1, 2-2, 1-3 (dont resolve)
                # 3-1, 3-1, 0-4 (eliminate 3, new tb 1&2)
                # 4-0, 1-3, 1-3 (promote 1, new tb 2&3)
                # 4-0, 2-2, 0-4 (order by score)
                scores = []
                for team, score in tied_teams.items():
                    scores.append(score["wins"])
                scores.sort(reverse=True)
                pass
                if scores == [4, 2, 0]:
                    possibility["standings"]["tie_broken"][tie_position] = True
                    for team, score in tied_teams.items():
                        if score["wins"] == 2:
                            possibility["standings"][team] += 1
                        elif score["wins"] == 0:
                            possibility["standings"][team] += 2
                elif scores == [4, 1, 1]:
                    possibility["standings"]["tie_broken"][tie_position] = True
                    for team, score in tied_teams.items():
                        if score["wins"] == 1:
                            possibility["standings"][team] += 1
                            if tie_position + 1 not in possibility["standings"]["tied_for"]:
                                possibility["standings"]["tied_for"].append(tie_position + 1)
                            possibility["standings"]["tie"][str(tie_position + 1)] = 2
                elif scores == [3, 3, 1]:
                    for team, score in tied_teams.items():
                        if score["wins"] == 1:
                            possibility["standings"][team] += 2
                        elif score["wins"] == 3:
                            possibility["standings"]["tied_for"].append(tie_position)
                            possibility["standings"]["tie"][str(tie_position)] = 2
                else:
                    possibility["standings"]["needs_tiebreaker"].add(tie_position)
                    for team in tied_teams.keys():
                        possibility["standings"]["tiebreaker_teams"].add(team)
            elif tie_count >= 4:
                possibility["standings"]["needs_tiebreaker"].add(tie_position)
                for team in tied_teams.keys():
                    possibility["standings"]["tiebreaker_teams"].add(team)
                pass
        pass


def eliminated(scenarios):
    scenario_counter = {}
    teamlist = []
    
    for team, details in teams.items():
        teamlist.append(team)
        scenario_counter[team] = {"scenarios": 0, "tiebreakers_req": 0}

    for possibility in scenarios:
        if possibility["standings"]["ties"] == "yes":
            tiebreaker(possibility)
        for team in teamlist:
            if possibility["standings"][team] > config.PLAYOFFS_CUTOFF_POSITION:
                scenario_counter[team]["scenarios"] += 1

    return scenario_counter

def locked(scenarios):
    scenario_counter = {}
    teamlist = []
    
    for team, details in teams.items():
        teamlist.append(team)
        scenario_counter[team] = {"scenarios": 0, "tiebreakers_req": 0}

    for possibility in scenarios:
        cutoff = config.PLAYOFFS_CUTOFF_POSITION + 1
        if possibility["standings"]["ties"] == "yes":
            for tie_position in possibility["standings"]["tied_for"]:
                tie_count = possibility["standings"]["tie"][str(tie_position)]
                if tie_position <= config.PLAYOFFS_CUTOFF_POSITION < tie_position + tie_count - 1:
                    tiebreaker(possibility)

                    if tie_position + tie_count - 1 > config.PLAYOFFS_CUTOFF_POSITION and possibility["standings"]["tie_broken"].get(tie_position) != True:
                        cutoff = tie_position

        for team in teamlist:     
            if possibility["standings"][team] < cutoff:
                scenario_counter[team]["scenarios"] += 1
            
    return scenario_counter

def maybe(scenarios):
    scenario_counter = {}
    teamlist = []

    for team, details in teams.items():
        teamlist.append(team)
        scenario_counter[team] = {"scenarios": 0, "tiebreakers_req": 0}

    for possibility in scenarios:
        tiebreaker(possibility)
        for team in teamlist:
            if possibility["standings"][team] <= config.PLAYOFFS_CUTOFF_POSITION:
                scenario_counter[team]["scenarios"] += 1
                if len(possibility["standings"]["needs_tiebreaker"]):
                    if possibility["standings"][team] in possibility["standings"]["needs_tiebreaker"]:
                        scenario_counter[team]["tiebreakers_req"] += 1

    return scenario_counter

def whatmusthappen(possibilities, team, full):
    print(f'Total scenarios: {len(possibilities)}')
    match_matrix = []
    tiebreakers = []
    must_happen = []
    tiebreaker_count = 0
    maybe_tiebreaker_against = {}

    for possibility in possibilities:
        tiebreaker(possibility)
        if possibility["standings"][team] <= config.PLAYOFFS_CUTOFF_POSITION:
            result_set = []
            for match in possibility["matches"]:
                for opponent in match["opponents"]:
                    if opponent == match["winner"]:
                        winner = opponent
                    else:
                        loser = opponent
                result_set.append((winner, loser))
            match_matrix.append(result_set)
            if len(possibility["standings"]["needs_tiebreaker"]):
                if possibility["standings"][team] in possibility["standings"]["needs_tiebreaker"]:
                    tiebreakers.append(True)
                    tiebreaker_count += 1
                    tie_list = list(possibility["standings"]["tiebreaker_teams"])
                    tie = tuple(sorted(tie_list))
                    if maybe_tiebreaker_against.get(tie):
                        maybe_tiebreaker_against[tie] += 1
                    else:
                        maybe_tiebreaker_against[tie] = 1
                    
                else:
                    tiebreakers.append(False)

    if len(match_matrix):
        print(f"There are only {len(match_matrix)} scenarios where {team} makes playoffs.")
        for i in range(len(match_matrix[0])):
            uniques = set()
            for i2 in range(len(match_matrix)):
                uniques.add(match_matrix[i2][i])
            if len(uniques) == 1 and uniques != whatifoutcomes:
                must_happen.append(list(uniques)[0])

        if len(must_happen) and len(must_happen) < len(possibilities):
            print(f"\nIn order for {team} to make playoffs:")
            must_happen.sort(key=lambda a: a[0])
            for game in must_happen:
                print(f"{game[0]} must beat {game[1]}")

            if full:
                print("")
                for i, match in enumerate(match_matrix):
                    for game in match:
                        print(f"{game[0]} beat {game[1]}, ", end="")
                    if tiebreakers[i]:
                        print(f"[TB REQ]", end="")
                    print("")

        if len(match_matrix) == tiebreaker_count:
            print("\nThey must win a tiebreaker.")
            print("\nMay be against:")
            for tiebreak_opponent, scenarios in maybe_tiebreaker_against.items():
                for opponent in tiebreak_opponent:
                    print(f"{opponent}, ", end="")
                print(f"({scenarios} scenarios)")
        elif tiebreaker_count > 0:
            print(f"\nThey must win a tiebreaker in {tiebreaker_count} of {len(match_matrix)} scenarios")
            print("\nMay be against:")
            for tiebreak_opponent, scenarios in maybe_tiebreaker_against.items():
                for opponent in tiebreak_opponent:
                    print(f"{opponent}, ", end="")
                print(f"({scenarios} scenarios)")
            print("")

        else:
            print(f"\nThere are no 'must happen' scenarios for {team} to make playoffs.")
    else:
        print(f"{team} cannot make playoffs.")

def implications(possibilities):
    print(f'Total scenarios: {len(possibilities)}')

    print("If ", end="")
    for match in whatifoutcomes:
        print(f"{match[0]} beats {match[1]}, ")

    new_possibilities = []
    for possibility in possibilities:
        poss_matches = generate_whatifs(possibility)
        if whatifoutcomes.issubset(poss_matches):
            new_possibilities.append(possibility)

    print(f'There are now only {len(new_possibilities)} scenarios')

    locked_scenarios = locked(possibilities)
    locked_after_whatif = locked(new_possibilities)
    locked_now = set()
    locked_after = set()
    for team, scenario_count in locked_scenarios.items():
        if scenario_count == len(possibilities):
            locked_now.add(team)

    for team, scenario_count in locked_after_whatif.items():
        if scenario_count == len(new_possibilities):
            locked_after.add(team)

    if locked_now != locked_after:
        if len(locked_now.difference(locked_after)):
            print(f"No longer locked: {locked_now.difference(locked_after)}")
            for team in locked_after.difference(locked_now):
                print(team)
        if len(locked_after.difference(locked_now)):
            for team in locked_after.difference(locked_now):
                print(f"{team} makes playoffs.")

    eliminated_scenarios = eliminated(possibilities)
    eliminated_after_whatif = eliminated(new_possibilities)
    eliminated_now = set()
    eliminated_after = set()
    for team, scenario_count in eliminated_scenarios.items():
        if scenario_count == len(possibilities):
            eliminated_now.add(team)

    for team, scenario_count in eliminated_after_whatif.items():
        if scenario_count == len(new_possibilities):
            eliminated_after.add(team)

    if eliminated_now != eliminated_after:
        if len(eliminated_now.difference(eliminated_after)):
            for team in eliminated_after.difference(eliminated_now):
                print(f"{team} is no longer eliminated.")
        if len(eliminated_after.difference(eliminated_now)):
            for team in eliminated_after.difference(eliminated_now):
                print(f"{team} is eliminated.")

def show_tiebreakers(possibilities):
    tiebreakers_required_count = 0
    possible_tiebreakers = {}
    for possibility in possibilities:
        tiebreaker(possibility)
        if len(possibility["standings"]["needs_tiebreaker"]):
            tiebreakers_required_count += 1
            tie_list = list(possibility["standings"]["tiebreaker_teams"])
            tie = tuple(sorted(tie_list))
            if possible_tiebreakers.get(tie):
                possible_tiebreakers[tie] += 1
            else:
                possible_tiebreakers[tie] = 1
    if tiebreakers_required_count != len(possibilities):
        print("Tiebreakers may not be required.")
    else:
        print("Tiebreakers are required.")
    
    if tiebreakers_required_count:
        print(f"\nTiebreakers occur in {tiebreakers_required_count} of {len(possibilities)}scenarios.")
        tiebreaker_list = []
        for tiebreaker_teams, count in possible_tiebreakers.items():
            tiebreaker_list.append((tiebreaker_teams, count))
        
        tiebreaker_list.sort(key=lambda a: a[1], reverse=True)

        for tiebreaker_scenario in tiebreaker_list:
            for team in tiebreaker_scenario[0]:
                print(f"{team}, ", end="")
            print(f"({tiebreaker_scenario[1]})")

def generate_whatifs(possibility):
    returnset = set()
    for match in possibility["matches"]:
        matchresult = [match["winner"]]
        for team in match["opponents"]:
            if team == match["winner"]:
                winner = team
            else:
                loser = team
        matchtuple = (winner, loser)
        returnset.add(matchtuple)
    return returnset

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, default='all', choices=['locked', 'eliminated', 'maybe', 'whatneedstohappen','whatchanges','all','tiebreakers'], help="""The command you want to run.
    "locked": shows teams that have secured a playoff spot.
    "eliminated": shows teams that cannot make playoffs, no matter what happens.
    "maybe": shows the number of scenarios in which it's possible for a team to make playoffs.
    "whatneedstohappen": specify with a team to check for conditions they need in order to qualify.
    "whatchanges": use the whatif file to see what changes in lock/elimination
    "tiebreakers": show tiebreaker info
    """)
    parser.add_argument('--team', type=str, default=None, help="specify a team tricode when using 'whatneedstohappen' for them to make it")
    parser.add_argument('--full', action='store_true', help="add to show full what needs to happen scenarios")
    parser.add_argument('--whatif', action='store_true', help="add to use the hypothetical scenarios in whatif.py")

    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    with open(f'{config.SERIES}.json') as json_file:
        possibilities = json.load(json_file)
        teams = possibilities.pop(0)
        previous_matches = possibilities.pop(0)

        if args.whatif:
            new_possibilities = []
            for possibility in possibilities:
                poss_matches = generate_whatifs(possibility)
                if whatifoutcomes.issubset(poss_matches):
                    new_possibilities.append(possibility)
            possibilities = new_possibilities

        if args.command == 'all':
            locked_scenarios = locked(possibilities)
            print(f"The following teams are locked in all {len(possibilities)} scenarios:")
            for team, scenario_count in locked_scenarios.items():
                if scenario_count["scenarios"] == len(possibilities):
                    print(f"{team} ")
             
            print("\nThe following can possibly make playoffs in X scenarios:")
            maybe_scenarios = maybe(possibilities)
            maybe_teams = []
            for team, scenario_count in maybe_scenarios.items():
                if len(possibilities) > scenario_count["scenarios"] > 0:
                    tiebreaker_req = scenario_count.get("tiebreakers_req")
                    maybe_teams.append((team,scenario_count["scenarios"],tiebreaker_req))
            maybe_teams.sort(key=lambda a: a[1])
            for team in maybe_teams:
                print(f"{team[0]}: {team[1]}", end="")
                if team[2]:
                    print(f" (tiebreakers required in {team[2]})", end="")
                print("")
                
            eliminate_scenarios = eliminated(possibilities)
            print(f"\nThe following teams are eliminated in all {len(possibilities)} scenarios:")
            for team, scenario_count in eliminate_scenarios.items():
                if scenario_count["scenarios"] == len(possibilities):
                    print(f"{team} ")

        if args.command == 'locked':
            locked_scenarios = locked(possibilities)
            print(f"The following teams are locked in all {len(possibilities)} scenarios:")
            for team, scenario_count in locked_scenarios.items():
                if scenario_count["scenarios"] == len(possibilities):
                    print(f"{team} ")

        if args.command == 'eliminated':
            eliminate_scenarios = eliminated(possibilities)
            print(f"The following teams are eliminated in all {len(possibilities)} scenarios:")
            for team, scenario_count in eliminate_scenarios.items():
                if scenario_count["scenarios"] == len(possibilities):
                    print(f"{team} ")
        
        if args.command == 'maybe':
            print("\nThe following can possibly make playoffs in X scenarios:")
            maybe_scenarios = maybe(possibilities)
            maybe_teams = []
            for team, scenario_count in maybe_scenarios.items():
                if len(possibilities) > scenario_count["scenarios"] > 0:
                    tiebreaker_req = scenario_count.get("tiebreakers_req")
                    maybe_teams.append((team,scenario_count["scenarios"],tiebreaker_req))
            maybe_teams.sort(key=lambda a: a[1])
            for team in maybe_teams:
                print(f"{team[0]}: {team[1]}", end="")
                if team[2]:
                    print(f" (tiebreakers required in {team[2]})", end="")
                print("")

        if args.command =='whatneedstohappen':
            if args.team is not None and args.team in teams:
                whatmusthappen(possibilities, args.team, args.full)
            else:
                print("No team entered or team not found")

        if args.command == 'tiebreakers':
            show_tiebreakers(possibilities)

        if args.command == 'whatchanges':
            implications(possibilities)
