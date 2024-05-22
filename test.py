from requests import get as get_from

url = "https://api.openligadb.de/getmatchdata/bl1/2023/1"
response = get_from(url)
data = response.json()

for game in data:
    team1_name = game['team1']['teamName']
    team2_name = game['team2']['teamName']

    result = game["matchResults"][1]
    team1_goals = result["pointsTeam1"]
    team2_goals = result["pointsTeam2"]
    
    print(f"{team1_name} vs {team2_name}: {team1_goals}-{team2_goals}")