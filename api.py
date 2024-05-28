from requests import get as get_from

def get_games(matchday="1", season="2024", tournament="em"):
    url = f"https://api.openligadb.de/getmatchdata/{tournament}/{season}/{matchday}"
    response = get_from(url)
    data = response.json()

    games = []

    for raw_game in data:
        game = dict()

        game["date"] = raw_game["matchDateTime"]
        game["team1"] = raw_game['team1']['teamName']
        game["team2"] = raw_game['team2']['teamName']
        game["location"] = raw_game["location"]["locationCity"]

        result = raw_game["matchResults"]
        try:
            game["result"] = f"{result[1]["pointsTeam1"]}:{result[1]["pointsTeam2"]}"
        except(IndexError):
            game["result"] = None

    print(game)

get_games()