from flask import Flask, jsonify, redirect, url_for # Capital letter for class imports
from flask_restful import Api, Resource, reqparse
import requests # Make get requests
from datetime import datetime
import json

app = Flask(__name__)
api = Api(app)

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

# Wrapper of PGA API that formats data how I need it
@app.route('/', methods=['GET'])
def showTournament():
    return redirect(url_for('getTournament'))

@app.route('/tournament', methods=['GET'])
def getTournament():
    if cur_tour_id != -1:
        response = {}
        response['Tour'] = 'PGA Tour'
        response['CurrentTournament'] = cur_tourny_data['debug']['tournament_in_schedule_file_name']
        response['LastUpdated'] = datetime.strptime(cur_tourny_data['last_updated'], '%Y-%m-%dT%H:%M:%S').strftime('%m/%d/%Y at %I:%M%p EST')
        response['Date'] = generateDate(cur_tourny_data['leaderboard']['start_date']) + " - " + generateDate(cur_tourny_data['leaderboard']['end_date'])
        response['Rounds'] = cur_tourny_data['leaderboard']['total_rounds']
        response['CurrentRound'] = cur_tourny_data['leaderboard']['current_round']
        response['Course'] = cur_tourny_data['leaderboard']['courses'][0]['course_name']
        return jsonify(dict(statusCode=200, body=response))
    else:
        return jsonify(dict(statusCode=404, body="No Current Tournaments"))

@app.route('/players', methods=['GET'])
def getPlayers():
    if cur_tour_id != -1:
        response = {}
        response['Players'] = grabAllPlayers()
        return jsonify(dict(statusCode=200, body=response))
    else:
        return jsonify(dict(statusCode=404, body="No Current Tournaments or Players"))

@app.route('/players/<string:name>', methods=['GET'])
def getPlayerWithName(name):
    if cur_tour_id != -1:
        for player in grabAllPlayers():
            if player['Name'] == name:
                return jsonify(dict(statusCode=200, body=player))

        return jsonify(dict(statusCode=404, body="Player is not in the current tournament"))


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

if __name__ == "__main__":
    app.run(debug=True)
