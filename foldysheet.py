from pprint import pprint
import requests
import config
import logging

logging.basicConfig(filename='example.log', level=logging.DEBUG)

series = "lcs"
series_url = f"https://api.pandascore.co/series/running?search[slug]={series}"
token = config.TOKEN
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(series_url, headers = headers)

slug = response.json()[0]["slug"]

match_url = f"https://api.pandascore.co/series/{slug}/matches?per_page=100&sort=scheduled_at"

response = requests.get(match_url, headers = headers)
matches = response.json()
teams = {}

for match in matches:
    for team in match["opponents"]:
        logging.debug(f'getting {team["opponent"]["acronym"]}')
        if not teams.get(team["opponent"]["acronym"]):
            a_team = team["opponent"]["acronym"]
            teams[a_team] = {"slug": team["opponent"]["slug"]}
            logging.debug(f"adding {a_team}")
    a_team = team["opponent"]["acronym"]
    try:
        winner = match['winner']['acronym']
    except Exception as e:
        winner = None
    
    if winner is not None:
        if teams[winner].get("wins"):
            teams[winner]["wins"] += 1
        else:
            teams[winner]["wins"] = 1

print(f"found {len(matches)} matches and {len(teams)} teams")
pprint(f"{teams}")


# TEAMS = {"TL", "C9", "TSM", "DIG", "100T", "EG", "IMT", "FLY", "CLG", "GG"}
# ROUNDS = 3

# match_list = []
# played_this_round = []

# for team in TEAMS:
#     for team2 in TEAMS:
#         match = {}
#         teams_in_this_match = [team, team2]
#         teams_in_this_match.sort()
#         if teams_in_this_match not in played_this_round and team is not team2:
#             match["teams"] = teams_in_this_match
#             played_this_round.append(teams_in_this_match)
#             match_list.append(match)

# print(f"total {len(match_list)}")
# print(match_list)