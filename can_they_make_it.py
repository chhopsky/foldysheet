import json
import argparse
import sys
import logging
import config

def eliminated(scenarios):
    scenario_counter = {}
    teamlist = []
    
    for team, details in teams.items():
        teamlist.append(team)
        scenario_counter[team] = 0

    for possibility in scenarios:
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