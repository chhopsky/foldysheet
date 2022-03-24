import json
import argparse
import sys
import logging
import config
import dateutil.parser

def tiebreaker(possibility):
    for tie_position in possibility["standings"]["tied_for"]:
        tie_count = possibility["standings"]["tie"][str(tie_position)]
        cutoff = config.PLAYOFFS_CUTOFF_POSITION
        if tie_position <= cutoff > tie_position + tie_count - 1:
            possibility["standings"]["tie_broken"] = {tie_position: False}
            tied_teams = {}
            tie_data = { "complete": True, "sov": []}
            for key, value in possibility["standings"].items():
                if value == tie_position:
                    tied_teams[key] = { "wins": 0, "sov": [] }

            for match in previous_matches:
                if match["status"] == "finished":
                    winner = match["winner"]["acronym"]
                    if winner in tied_teams.keys():
                        tied_teams[winner]["wins"] += 1
                        match_start = dateutil.parser.isoparse(match["begin_at"])
                        match_end = dateutil.parser.isoparse(match["end_at"])
                        match_time = match_end - match_start
                        for team in match["opponents"]:
                            opponent = team["opponent"]["acronym"]
                            if opponent != winner:
                                tie_data["sov"].append((winner, match_time.seconds))
            
            for unfinished_match in possibility["matches"]:
                winner = unfinished_match["winner"]
                if winner in tied_teams.keys():
                    tied_teams[winner]["wins"] += 1
                    tie_data["complete"] = False

            if tie_count == 2:
                # check played matches

                for team, score in tied_teams.items():
                    if score["wins"] == 0:
                        possibility["standings"][team] += 1
                        possibility["standings"]["tie_broken"][tie_position] = True
                    if score["wins"] == 1 and tie_data["complete"] == True:
                        tie_data["sov"].sort(key=lambda a: a[1])
                        if tie_data["sov"][0] == team:
                            possibility["standings"][team] += 1
                            possibility["standings"]["tie_broken"][tie_position] = True
                            
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
                            possibility["standings"]["tied_for"].append(tie_position + 1)
                            possibility["standings"]["tie"][str(tie_position + 1)] = 2
                elif scores == [3, 3, 1]:
                    for team, score in tied_teams.items():
                        if score["wins"] == 1:
                            possibility["standings"][team] += 2
                        elif score["wins"] == 3:
                            possibility["standings"]["tied_for"].append(tie_position)
                            possibility["standings"]["tie"][str(tie_position)] = 2
            elif tie_count >= 4:
                # we are fucked. it's playoffs baybee
                pass


def eliminated(scenarios):
    scenario_counter = {}
    teamlist = []
    
    for team, details in teams.items():
        teamlist.append(team)
        scenario_counter[team] = 0

    for possibility in scenarios:
        if possibility["standings"]["ties"] == "yes":
            tiebreaker(possibility)
        for team in teamlist:
            if possibility["standings"][team] > config.PLAYOFFS_CUTOFF_POSITION:
                scenario_counter[team] += 1

    return scenario_counter

def locked(scenarios):
    scenario_counter = {}
    teamlist = []
    
    for team, details in teams.items():
        teamlist.append(team)
        scenario_counter[team] = 0

    for possibility in scenarios:
        cutoff = config.PLAYOFFS_CUTOFF_POSITION + 1
        if possibility["standings"]["ties"] == "yes":

            tiebreaker(possibility)

            for tie in possibility["standings"]["tied_for"]:
                if tie + possibility["standings"]["tie"][str(tie)] - 1 > config.PLAYOFFS_CUTOFF_POSITION:
                    cutoff = tie

        for team in teamlist:     
            if possibility["standings"][team] < cutoff:
                scenario_counter[team] += 1
            
    return scenario_counter

def maybe(scenarios):
    scenario_counter = {}
    teamlist = []

    print(f'Total scenarios: {len(scenarios)}')

    for team, details in teams.items():
        teamlist.append(team)
        scenario_counter[team] = 0

    for possibility in scenarios:
        for team in teamlist:
            if possibility["standings"][team] <= config.PLAYOFFS_CUTOFF_POSITION:
                scenario_counter[team] += 1
    
    locked_scenarios = locked(possibilities.copy())
    locked_teams = []
    for lock_team, lock_scenario in locked_scenarios.items():
        if lock_scenario == len(possibilities):
            locked_teams.append(lock_team)
            
    print("The following can possibly make playoffs in X scenarios:")
    for team, scenario_count in scenario_counter.items():
        if scenario_count > 0 and team not in locked_teams:
            print(f"{team}: {scenario_count}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, choices=['locked', 'eliminated', 'maybe', 'whatneedstohappen'], help='The command you want to run.')

    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    with open(f'{config.SERIES}.json') as json_file:
        possibilities = json.load(json_file)
        teams = possibilities.pop(0)
        previous_matches = possibilities.pop(0)

        if args.command == 'locked':
            locked_scenarios = locked(possibilities)
            print(f"The following teams are locked in all {len(possibilities)} scenarios:")
            for team, scenario_count in locked_scenarios.items():
                if scenario_count == len(possibilities):
                    print(f"{team} ")

        if args.command == 'eliminated':
            eliminate_scenarios = eliminated(possibilities)
            print(f"The following teams are eliminated in all {len(possibilities)} scenarios:")
            for team, scenario_count in eliminate_scenarios.items():
                if scenario_count == len(possibilities):
                    print(f"{team} ")
        
        if args.command == 'maybe':
            maybe(possibilities)

        #if args.command =='whatneedstohappen':
# def check_possibilities(team, condition):