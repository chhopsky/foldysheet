from pprint import pprint
import requests
import config
import logging
import json

def bin_str(number):
    return bin(number)[2:]

logging.basicConfig(filename='example.log', level=logging.DEBUG)

series_url = f"https://api.pandascore.co/series/running?search[slug]={config.SERIES}"
token = config.TOKEN
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(series_url, headers = headers)

slug = response.json()[0]["slug"]

match_url = f"https://api.pandascore.co/series/{slug}/matches?per_page=100&sort=scheduled_at"

response = requests.get(match_url, headers = headers)
matches = response.json()
f = open("lastrequest.json", "w")
f.write(json.dumps(matches))
f.close()
teams = {}
unplayed_matches = []

for match in matches:
    for team in match["opponents"]:
        logging.debug(f'getting {team["opponent"]["acronym"]}')
        if not teams.get(team["opponent"]["acronym"]):
            a_team = team["opponent"]["acronym"]
            teams[a_team] = {"slug": team["opponent"]["slug"],
            "acronym": a_team,
            "wins": 0}
            logging.debug(f"adding {a_team}")
    a_team = team["opponent"]["acronym"]
    try:
        winner = match['winner']['acronym']
    except Exception as e:
        winner = None
    
    if winner is not None:
        teams[winner]["wins"] += 1
    elif match["tournament"]["name"] == "Regular":
        unplayed_matches.append(match)

print(f"found {len(matches)} matches and {len(teams)} teams")

print("Standings:")
i = 18
while i >= 0:
    for tricode, team in teams.items():
        if team["wins"] == i:
            print(f'{team["slug"]}: {team["wins"]}')
    i = i - 1

unplayed_match_count = len(unplayed_matches)
total_possibilities = 2 ** unplayed_match_count
print(f"\nUnplayed matches: {unplayed_match_count}")
print(f"Total possibilities: {total_possibilities}")
print(f"Binary representation: {bin_str(total_possibilities)}")

possibilities = []
possibilities.append(teams)
possibilities.append(matches)

# calculate every possible combination of outcomes of every match
i = 0
while i < total_possibilities:
    wins = bin_str(i).rjust(unplayed_match_count, '0')
    possibility = {"standings" : {}, "matches": []}

    for key, value in teams.items():
        possibility["standings"][key] = value["wins"]

    for num, match in enumerate(unplayed_matches):
        # match["winner"] = match["opponents"][int(wins[num])]
        possible_match = {"num": num, "opponents": []}
        for team in match["opponents"]:
            possible_match["opponents"].append(team["opponent"]["acronym"])
        possible_match["winner"] = match["opponents"][int(wins[num])]["opponent"]["acronym"]
        possibility["standings"][possible_match["winner"]] += 1
        possibility["matches"].append(possible_match)
        #possibility.append(possibility_teams)

        #get the actual valid counts of wins
    standings = {"standings": {}}
    order = []

    # empty list for each win number
    for key, value in possibility["standings"].items():
        standings["standings"][value] = []
    
    # add each team to their number of wins
    for key, value in possibility["standings"].items():
        standings["standings"][value].append(key)

    # create a list of the win numbers
    for key, value in standings["standings"].items():
        order.append(key)
    
    order.sort(reverse = True)

    actual_standings = {"ties": "no", "tied_for": [], "tie": {}, "tie_broken": {}}
    rank = 1

    for win_count in order:
        for rank_team in standings["standings"][win_count]:
            actual_standings[rank_team] = rank
        
        if len(standings["standings"][win_count]) > 1:
            actual_standings["ties"] = "yes"
            actual_standings["tie_broken"][rank] = False
            actual_standings["tied_for"].append(rank)
            actual_standings["tie"][rank] = len(standings["standings"][win_count])
        rank += len(standings["standings"][win_count])

    possibility["standings"] = actual_standings
    possibilities.append(possibility)
    i = i + 1

f = open(f"{config.SERIES}.json", "w")
f.write(json.dumps(possibilities))
f.close()

print(f"All possible outcomes written to {config.SERIES}.json. Run can_they_make_it.py to analyze.")
