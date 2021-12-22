# run this with uvicorn main:app and go to http://localhost:8000
# for testing go to http://localhost:8000/docs

from typing import Awaitable
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sqlite3
import json
import random

con = sqlite3.connect('CAH.db') # connects to the database
cur = con.cursor() # creates a cursor

app = FastAPI()

@app.get("/answer_card/{card_id}")
async def answer_card(card_id: int):
    # returns the answer card with id card_id
    card = cur.execute(f"SELECT * FROM AnswerCards WHERE id = {card_id}").fetchone()
    # returns the card in the form of a dictionary
    return {
        "id": card[0],
        "text": card[1],
    }

@app.get("/question_card/{card_id}")
async def question_card(card_id: int):
    # returns the question card with id card_id
    card = cur.execute(f"SELECT * FROM QuestionCards WHERE id = {card_id}").fetchone()
    # returns the card in the form of a dictionary
    return {
        "id": card[0],
        "text": card[1],
        "num_gaps": card[2]
    }

@app.post("/deal_qcard/{game_id}")
async def deal_qcard(game_id: int):
    keep_going = True
    max_qcard = await num_question_cards()
    last_qcard = cur.execute(f"SELECT QCard FROM Games WHERE id = {game_id}").fetchone()[0]
    while keep_going:
        rand_int = random.randint(1, max_qcard)
        if rand_int != last_qcard:
            keep_going = False
    cur.execute(f"UPDATE Games SET QCard = '{rand_int}' WHERE id = {game_id}")
    q_card = await question_card(rand_int)
    return q_card["text"]

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
async def czar(game_id: int, player_id: int):
    czar_id = cur.execute(f"SELECT CzarID FROM Games WHERE id = {game_id}").fetchone()[0]
    if czar_id == player_id:
        Czar = True
    else:
        Czar = False
    return Czar

@app.post("/create_player")
async def create_player():
    cur.execute("INSERT INTO Players (ListCards, points) VALUES ('[]', 0)")
    con.commit()
    return cur.lastrowid

@app.post("/return_cards/{player_id}")
async def return_cards(player_id: int):
    PlayersCards = cur.execute(f"SELECT ListCards FROM Players WHERE id = {player_id}").fetchone()
    return PlayersCards[0]

@app.post("/deal_cards/{player_id}")
async def deal_cards(player_id: int):
    max_cards = 7
    num_players = []
    number_cards = 0
    temp_list = []
    player_id = int(player_id)
    max_a_cards = await num_answer_cards()
    for index in cur.execute("SELECT id FROM Players"):
        num_players.append(index[0])
    unused_cards = []
    for index in range(max_a_cards):
        unused_cards.append(index + 1)
    for ids in num_players:
        list_cards = cur.execute(f"SELECT ListCards FROM Players WHERE id = {ids}").fetchone()[0]
        list_cards = json.loads(list_cards)
        for cards in list_cards:
            unused_cards.remove(cards)
            if (ids) == player_id:
                number_cards += 1
    list_cards = cur.execute(f"SELECT ListCards FROM Players WHERE id = {player_id}").fetchone()[0]
    list_cards = json.loads(list_cards)
    for index in range(max_cards - number_cards):
        random_num = random.randint(1, len(unused_cards))
        list_cards.append(unused_cards[random_num])
        unused_cards.pop(random_num)
    cur.execute(f"UPDATE Players SET ListCards = '{list_cards}' WHERE id = {player_id}")
    for card_id in list_cards:
        acard = await answer_card(card_id)
        acard = acard["text"]
        temp_list.append(acard)
    list_cards = temp_list
    con.commit()
    return list_cards

@app.post("/create_game")
async def create_game():
    cur.execute(f"INSERT INTO Games (ListPlayerID) VALUES ('[]')")
    game_id = cur.lastrowid
    q_card = await deal_qcard(game_id)
    con.commit()
    return game_id, q_card

@app.post("/join_game/{game_id}/{player_id}")
async def join_game(player_id: int, game_id: int):
    list_players = cur.execute(f"SELECT ListPlayerID FROM Games WHERE id = {game_id}").fetchone()[0]
    list_players = json.loads(list_players)
    list_players.append(player_id)
    cur.execute(f"UPDATE Games SET ListPlayerID = '{list_players}' WHERE id = {game_id}")
    cur.execute(f"UPDATE Games SET CzarID = {player_id} WHERE id = {game_id}")
    con.commit()

@app.post("/save_choice/{player_id}/{choice}")
async def save_choice(player_id: int, choice: str):
    choice = json.loads(choice)
    player_cards = cur.execute(f"SELECT ListCards FROM Players WHERE id = {player_id}").fetchone()[0]
    player_cards = json.loads(player_cards)
    choice_ids = []
    for index in choice:
        choice_ids.append(player_cards[index - 1])
    cur.execute(f"UPDATE Players SET choice = '{choice_ids}' WHERE id = {player_id}")
    con.commit()

@app.post("/delete_game/{game_id}")
async def delete_game(game_id: int):
    cur.execute(f"DELETE FROM Games WHERE id = {game_id}")
    con.commit()

@app.post("/delete_player/{player_id}")
async def delete_player(player_id: int):
    cur.execute(f"DELETE FROM Players WHERE id = {player_id}")
    con.commit()

@app.get("/return_num_players/{game_id}")
async def return_num_players(game_id: int):
    list_player_id = cur.execute(f"SELECT ListPlayerID FROM Games WHERE id = {game_id}").fetchone()[0]
    list_player_id = json.loads(list_player_id)
    return len(list_player_id)

@app.get("/return_qcard/{game_id}")
async def return_qcard(game_id: int):
    q_card_id = cur.execute(f"SELECT QCard FROM Games WHERE id = {game_id}").fetchone()[0]
    q_card = await question_card(q_card_id)
    num_gaps = q_card["num_gaps"]
    q_card = q_card["text"]
    return q_card, num_gaps

@app.get("/return_choices/{game_id}")
async def return_choices(game_id: int):
    choice_in = True
    list_choices = []
    list_players = cur.execute(f"SELECT ListPlayerID FROM Games WHERE id = {game_id}").fetchone()[0]
    list_players = json.loads(list_players)
    czar_id = cur.execute(f"SELECT CzarID FROM Games WHERE id = {game_id}").fetchone()[0]
    list_players.remove(czar_id)
    for player_id in list_players:
        choice = cur.execute(f"SELECT choice FROM Players WHERE id = {player_id}").fetchone()[0]
        try:
            choice = json.loads(choice)
            list_choices.append((player_id, choice))
        except:
            choice_in = False
            break
    return choice_in, list_choices 

@app.post("/give_points/{czar_id}/{point_winner}")
async def give_points(czar_id: int, point_winner: int):
    cur.execute(f"UPDATE Players SET choice = '{point_winner}' WHERE id = {czar_id}")
    points = cur.execute(f"SELECT points FROM Players WHERE id = {point_winner}").fetchone()[0]
    points += 1
    cur.execute(f"UPDATE Players SET points = '{points}' WHERE id = {point_winner}")
    con.commit()
    return points

@app.get("/return_czar_choice/{game_id}")
async def return_czar_choice(game_id: int):
    choice_in = False
    czar_id = cur.execute(f"SELECT CzarID FROM Games WHERE id = {game_id}").fetchone()[0]
    czar_choice = cur.execute(f"SELECT choice FROM Players WHERE id = {czar_id}").fetchone()[0]
    if czar_choice != None:
        choice_in = True
    return choice_in, czar_choice

@app.get("/")
async def root():
    #returns the front end code so that it can be run
    return HTMLResponse(open("CAH.html", "rt").read())
