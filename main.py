# run this with uvicorn main:app and go to http://localhost:8000
# for testing go to http://localhost:8000/docs

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sqlite3
import json
import random

con = sqlite3.connect('CAH.db') # connects to the database
cur = con.cursor() # creates a cursor

app = FastAPI()

@app.get("/answer_card/{card_id}")
async def answer_card(card_id):
    # returns the answer card with id card_id
    card = cur.execute(f"SELECT * FROM AnswerCards WHERE id = {card_id}").fetchone()
    # returns the card in the form of a dictionary
    return {
        "id": card[0],
        "text": card[1],
    }

@app.get("/question_card/{card_id}")
async def question_card(card_id):
    # returns the question card with id card_id
    card = cur.execute(f"SELECT * FROM QuestionCards WHERE id = {card_id}").fetchone()
    # returns the card in the form of a dictionary
    return {
        "id": card[0],
        "text": card[1],
        "num_gaps": card[2]
    }

@app.get("/num_answer_cards")
async def num_answer_cards():
    # returns the maximum number of answer cards in the db
    # gets the max num in the form of a list
    count = cur.execute("SELECT COUNT() FROM AnswerCards").fetchone()
    # returns the value of the list
    return count[0]

@app.get("/num_question_cards")
async def num_question_cards():
    # returns the maximum number of question cards in the db
    # gets the max num in the form of a list 
    count = cur.execute("SELECT COUNT() FROM QuestionCards").fetchone()
    # returns the value of the list
    return count[0]

@app.get("/czar/{game_id}/{player_id}") 
async def czar(game_id, player_id):
    czar_id = cur.execute(f"SELECT CzarID FROM Games WHERE id = {game_id}").fetchone()[0]
    czar_id = json.loads(czar_id)
    if czar_id == player_id:
        Czar = True
    else:
        Czar = False
    return Czar

@app.post("/player_cards/{player_id}/{answer_card}")
async def player_cards(player_id, answer_card):
    hands_card = json.loads(cur.execute(f"SELECT ListCards FROM Players WHERE id = {player_id}"))
    hands_card.append(answer_card)
    cur.execute(f"UPDATE Players SET ListCards = '{hands_card}' WHERE id = {player_id}")
    con.commit()

@app.post("/create_player")
async def create_player():
    cur.execute("INSERT INTO Players (ListCards, points) VALUES ('[]', 0)")
    con.commit()
    return cur.lastrowid

@app.post("/return_cards/{player_id}")
async def return_cards(player_id):
    PlayersCards = cur.execute(f"SELECT ListCards FROM Players WHERE id = {player_id}").fetchone()
    return PlayersCards[0]

@app.post("/deal_cards/{player_id}")
async def deal_cards(player_id):
    max_cards = 7
    number_cards = 0
    player_id = int(player_id)
    max_a_cards = await num_answer_cards()
    num_players = cur.execute("SELECT COUNT() FROM Players").fetchone()[0]
    unused_cards = []
    for index in range(max_a_cards):
        unused_cards.append(index + 1)
    for ids in range(num_players):
        list_cards = cur.execute(f"SELECT ListCards FROM Players WHERE id = {ids + 1}").fetchone()[0]
        list_cards = json.loads(list_cards)
        for cards in list_cards:
            unused_cards.remove(cards)
            if (ids + 1) == player_id:
                number_cards += 1
    list_cards = cur.execute(f"SELECT ListCards FROM Players WHERE id = {player_id}").fetchone()[0]
    list_cards = json.loads(list_cards)
    for index in range(max_cards - number_cards):
        random_num = random.randint(1, len(unused_cards))
        list_cards.append(unused_cards[random_num])
        unused_cards.pop(random_num)
    cur.execute(f"UPDATE Players SET ListCards = '{list_cards}' WHERE id = {player_id}")
    con.commit()
    return list_cards

#    get number of answer_Cards
#    make a list that goes from 1 ro number of cards [1, 2, ...]
#    loop through players
#        remove from list any IDS that appea rin a players hand
#        if plaer is player_id then take note of how many cards they have
#    make an array of random cards size max cards - num player cards
#    update the database to reflect new cards held by player = playerid


#    list_cards = cur.execute(f"SELECT ListCards FROM Players WHERE id = {player_id}").fetchone()[0]
#    list_cards = json.loads(list_cards)
#    for index in range(max_a_cards):
#        card = await answer_card(index + 1)
#        unused_cards.append(card)
#    while len(list_cards) != max_cards:
#        rand_num = random.randint(1, len(unused_cards))
#        list_cards.append(unused_cards[rand_num])
#        unused_cards.pop(rand_num)
#    cur.execute(f"UPDATE Players SET ListCards = '{list_cards}' WHERE id = {player_id}")
#    return list_cards

@app.post("/create_game")
async def create_game():
    cur.execute(f"INSERT INTO Games (ListPlayerID) VALUES ('[]')")
    con.commit()
    return cur.lastrowid

@app.post("/join_game/{game_id}/{player_id}")
async def join_game(player_id, game_id):
    list_players = cur.execute(f"SELECT ListPlayerID FROM Games WHERE id = {game_id}").fetchone()[0]
    list_players = json.loads(list_players)
    list_players.append(player_id)
    cur.execute(f"UPDATE Games SET ListPlayerID = '{list_players}' WHERE id = {game_id}")
    cur.execute(f"UPDATE Games SET CzarID = '{player_id}' WHERE id = {game_id}")
    con.commit

@app.post("/save_choice/{player_id}/{choice}")
async def save_choice(player_id, choice):
    cur.execute(f"UPDATE Players SET choice = '{choice}' WHERE id = {player_id}")
    con.commit()

@app.get("/")
async def root():
    #returns the front end code so that it can be run
    return HTMLResponse(open("index.html", "rt").read())
