import json
import argparse
import sys
import logging

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str, choices=['made_playoffs', 'eliminated', 'scenarios_made', 'scenarios_tied', 'ties'], help='The command you want to run.')

    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    with open('output.json') as json_file:
        possibilities = json.load(json_file)
        teams = possibilities.pop(0)
        teamlist = []

        scenario_counter = {}

        for team, details in teams.items():
            teamlist.append(team)
            scenario_counter[team] = 0

        if args.command == 'made_playoffs':
            can_make_playoffs = teamlist.copy()
            scenario_count = 0
            print(f"Total possibilities: {len(possibilities)}")
            for possibility in possibilities:
                scenario_count += 1
                for item in possibility:
                    if item.get("ties"):
                        # print(item)
                        for team in teamlist:
                            # print(f"checking {team}")
                            if item[team] >= 6 and 6 not in item["tied_for"]:
                                scenario_counter[team] += 1
                                # print(f"{team} does not in this scenario")
                                try:
                                    can_make_playoffs.remove(team)
                                except ValueError:
                                    pass
                        # input("Press Enter to continue...")

            for each in can_make_playoffs:
                scenario_counter.pop(each)
            print(f"Checked {scenario_count} scenarios.")
            print(f"The following teams are locked for playoffs: {can_make_playoffs}")
            print(f"The following teams have X scenarios where they may not make it:")
            print(scenario_counter)
# def check_possibilities(team, condition):

    


