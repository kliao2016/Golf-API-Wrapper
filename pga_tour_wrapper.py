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

@app.route('/tournament/', methods=['GET'])
def getTournament():
    if cur_tour_id != -1:
        response = {}
        response['tour'] = 'PGA Tour'
        response['current_tournament'] = cur_tourny_data['debug']['tournament_in_schedule_file_name']
        response['last_updated'] = datetime.strptime(cur_tourny_data['last_updated'], '%Y-%m-%dT%H:%M:%S').strftime('%m/%d/%Y at %I:%M%p EST')
        response['date'] = generateDate(cur_tourny_data['leaderboard']['start_date']) + " - " + generateDate(cur_tourny_data['leaderboard']['end_date'])
        response['rounds'] = cur_tourny_data['leaderboard']['total_rounds']
        response['current_round'] = cur_tourny_data['leaderboard']['current_round']
        response['course'] = cur_tourny_data['leaderboard']['courses'][0]['course_name']
        response['total_par'] = cur_tourny_data['leaderboard']['courses'][0]['par_total']
        return jsonify(dict(statusCode=200, body=response))
    else:
        return jsonify(dict(statusCode=404, body="No Current Tournaments"))

@app.route('/players/', methods=['GET'])
def getPlayers():
    if cur_tour_id != -1:
        response = {}
        response['players'] = grabAllPlayers()
        return jsonify(dict(statusCode=200, body=response))
    else:
        return jsonify(dict(statusCode=404, body="No Current Tournaments or Players"))

@app.route('/players/<string:name>', methods=['GET'])
def getPlayerWithName(name):
    if cur_tour_id != -1:
        for player in grabAllPlayers():
            if player['name'] == name:
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
        playerData['name'] = player['player_bio']['first_name'] + " " + player['player_bio']['last_name']
        playerData['position'] = player['current_position']
        playerData['today_score'] = player['today']
        playerData['total_score'] = player['total']
        playerData['thru'] = player['thru']
        playerData['fedex_ranking'] = player['rankings']['cup_rank']
        playerData['fedex_points'] = player['rankings']['cup_points']
        playerData['projected_fedex_ranking'] = player['rankings']['projected_cup_rank']
        playerData['projected_fedex_points'] = player['rankings']['projected_cup_points_total']
        playerData['fedex_trailing_by'] = player['rankings']['cup_trailing']
        playerData['total_shots'] = player['total_strokes']
        playerData['rounds'] = grabPlayerRounds(player['rounds'])
        allPlayers.append(playerData)

    return allPlayers

# Helper function to grab all rounds and scores for a player in the tournament
def grabPlayerRounds(rounds):
    playerRounds = []
    for x in range(0, len(rounds)):
        playerRounds.append(rounds[x]['strokes'])

    return playerRounds

if __name__ == "__main__":
    app.run(debug=True)
