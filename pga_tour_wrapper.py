from flask import Flask # Capital letter for class imports
from flask_restful import Api, Resource, reqparse
import requests # Make get requests
from datetime import datetime

cur_tour_id = -1
tour_id_url = "https://statdata.pgatour.com/r/current/message.json"

# Grab the current tournament id
id_req = requests.get(url = tour_id_url)
id_req_data = id_req.json()

cur_tour_id = id_req_data['tid']

# Use the current tournament id to grab tournament stats
cur_tourny_url = "https://statdata.pgatour.com/r/" + cur_tour_id + "/leaderboard-v2mini.json"
cur_tourny_req = requests.get(cur_tourny_url)
cur_tourny_data = cur_tourny_req.json()

app = Flask(__name__)
api = Api(app)

# Wrapper of PGA API that formats data how I need it
class Tournament(Resource):
    def get(self):
        if cur_tour_id != -1:
            response = {}
            response['Tour'] = 'PGA Tour'
            response['CurrentTournament'] = cur_tourny_data['debug']['tournament_in_schedule_file_name']
            response['LastUpdated'] = datetime.strptime(cur_tourny_data['last_updated'], '%Y-%m-%dT%H:%M:%S').strftime('%m/%d/%Y at %I:%M%p EST')
            response['Date'] = generateDate(cur_tourny_data['leaderboard']['start_date']) + " - " + generateDate(cur_tourny_data['leaderboard']['end_date'])
            response['Rounds'] = cur_tourny_data['leaderboard']['total_rounds']
            response['CurrentRound'] = cur_tourny_data['leaderboard']['current_round']
            response['Course'] = cur_tourny_data['leaderboard']['courses'][0]['course_name']
            response['Players'] = grabAllPlayers()
            return response, 200
        else:
            return "No Current Tournaments", 404

# Helper function to change date format
def generateDate(date):
    dateObj = datetime.strptime(date,'%Y-%m-%d')
    return dateObj.strftime('%m/%d/%Y')

# Helper function to grab all players in the current tournament
def grabAllPlayers():
    allPlayers = []
    for player in cur_tourny_data['leaderboard']['players']:
        playerData = {}
        playerData['Name'] = player['player_bio']['first_name'] + " " + player['player_bio']['last_name']
        playerData['Position'] = player['current_position']
        playerData['TodayScore'] = player['today']
        playerData['TotalScore'] = player['total']
        playerData['Thru'] = player['thru']
        playerData['FedExRanking'] = player['rankings']['cup_rank']
        playerData['FedExPoints'] = player['rankings']['cup_points']
        playerData['ProjectedFedExRanking'] = player['rankings']['projected_cup_rank']
        playerData['ProjectedFedExPoints'] = player['rankings']['projected_cup_points_total']
        playerData['FedexTrailingBy'] = player['rankings']['cup_trailing']
        playerData['TotalShots'] = player['total_strokes']
        playerData['Rounds'] = grabPlayerRounds(player['rounds'])
        allPlayers.append(playerData)

    return allPlayers

# Helper function to grab all rounds and scores for a player in the tournament
def grabPlayerRounds(rounds):
    playerRounds = []
    for x in range(0, len(rounds)):
        roundInfo = {}
        roundInfo['Round'] = rounds[x]['round_number']
        roundInfo['Score'] = rounds[x]['strokes']
        playerRounds.append(roundInfo)

    return playerRounds

# Add API GET endpoint
api.add_resource(Tournament, "/tournaments")
app.run(debug=True)
