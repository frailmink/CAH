# run this with uvicorn main:app and go to http://localhost:8000
# for testing go to http://localhost:8000/docs

from ctypes import pointer
import string
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

@app.post("/reset_choices/{game_id}")
async def reset_choices(game_id: int):
    # resets the choices of the players in the db by giving them a (NULL) value
    list_players = cur.execute(f"SELECT ListPlayerID FROM Games WHERE id = {game_id}").fetchone()[0]
    list_players = json.loads(list_players)
    # loops through all the players and sets their choices to a null value
    for players in list_players:
        cur.execute(f"UPDATE Players SET choice = '(NULL)' WHERE id = {players}")
    con.commit()

@app.post("/change_czar/{game_id}")
async def change_czar(game_id: int):
    # changes the czar
    count = 0
    # gets previous czar
    czar_id = cur.execute(f"SELECT CzarID FROM Games WHERE id = {game_id}").fetchone()[0]
    list_players = cur.execute(f"SELECT ListPlayerID FROM Games WHERE id = {game_id}").fetchone()[0]
    list_players = json.loads(list_players)
    # finds the location of the czar's id in the list ListPlayers from the db 
    while czar_id != list_players[count]:
        count += 1
    # checks if the last czar was at the end of the list and if they were it sets the next czar to be the first one in the list
    if count == len(list_players) - 1:
        cur.execute(f"UPDATE Games SET CzarID = {list_players[0]} WHERE id = {game_id}")
    else:
        cur.execute(f"UPDATE Games SET CzarID = {list_players[count + 1]} WHERE id = {game_id}")
    con.commit()

@app.post("/remove_chosen_cards/{player_id}/{cards_chosen}")
async def remove_chosen_cards(player_id: int, cards_chosen: str):
    # removes the chosen answer cards of the players
    list_cards = cur.execute(f"SELECT ListCards FROM Players WHERE id = {player_id}").fetchone()[0]
    list_cards = json.loads(list_cards)
    cards_chosen = json.loads(cards_chosen)
    choice_ids = []
    # due to the fact that it only returns the location of the cards chosen this loops through them and appends the card ids to a list
    for index in cards_chosen:
        choice_ids.append(list_cards[index - 1])
    # loops through the answer card ids and removes them from the list of cards the player has from the db
    for card_id in choice_ids:
        list_cards.remove(card_id)
    cur.execute(f"UPDATE Players SET ListCards = '{list_cards}' WHERE id = {player_id}")
    con.commit()

@app.post("/deal_qcard/{game_id}")
async def deal_qcard(game_id: int):
    # changes the question card to a new one
    keep_going = True
    # gets number of question cards in the db
    max_qcard = await num_question_cards()
    last_qcard = cur.execute(f"SELECT QCard FROM Games WHERE id = {game_id}").fetchone()[0]
    # loops indefently until the new question card is not the same as the old question card
    while keep_going:
        # gets random number
        rand_int = random.randint(1, max_qcard)
        # checks if the random number is the same number as the old question card id
        if rand_int != last_qcard:
            keep_going = False
    # gets the question card from the db with the id gotten from the random number
    cur.execute(f"UPDATE Games SET QCard = '{rand_int}' WHERE id = {game_id}")
    q_card = await question_card(rand_int)
    return q_card["text"], q_card["num_gaps"]

@app.get("/check_game_finish/{game_id}/{points_to_win}")
async def check_game_finish(game_id: int, points_to_win: int):
    # checks if the game has finished
    # returns a true or false statement depending on whether the game has ended or not, as well as, the id of the winner if there was a winner
    winner_id = 0
    game_ended = False
    list_players = cur.execute(f"SELECT ListPlayerID FROM Games WHERE id = {game_id}").fetchone()[0]
    list_players = json.loads(list_players)
    #loops through all the players and checks if they have enoough points to win
    for player in list_players:
        points = cur.execute(f"SELECT points FROM Players WHERE id = {player}").fetchone()[0]
        #checks to see whether the player has won the game
        if points == points_to_win:
            game_ended = True
            winner_id = player
    #if any player has enough points to win it returns a true statament and if no one does it returns a false statement
    return game_ended, winner_id

@app.get("/num_points/{player_id}")
async def num_points(player_id: int):
    # returns the number of points the user with id player_id has
    # this function is going to be used in the frontend to check if the player has won the game
    points = cur.execute(f"SELECT points FROM Players WHERE id = {player_id}").fetchone()[0]
    # returns the points the user has
    return points

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
    # checks if the player is the current czar
    czar_id = cur.execute(f"SELECT CzarID FROM Games WHERE id = {game_id}").fetchone()[0]
    if czar_id == player_id:
        Czar = True
    else:
        Czar = False
    return Czar

@app.post("/create_player")
async def create_player():
    # creates a new player in the db
    cur.execute("INSERT INTO Players (ListCards, points) VALUES ('[]', 0)")
    con.commit()
    return cur.lastrowid

@app.post("/return_cards/{player_id}")
async def return_cards(player_id: int):
    # returns the answer cards in the players hand from the db
    PlayersCards = cur.execute(f"SELECT ListCards FROM Players WHERE id = {player_id}").fetchone()
    return PlayersCards[0]

@app.post("/deal_cards/{player_id}")
async def deal_cards(player_id: int):
    # deals the needed number of cards to get the players hand to 7 cards
    max_cards = 7
    num_players = []
    number_cards = 0
    temp_list = []
    player_id = int(player_id)
    # gets the maximum number of answer cards
    max_a_cards = await num_answer_cards()
    # loops through all the players in the db and appends their ids to a list
    for index in cur.execute("SELECT id FROM Players"):
        num_players.append(index[0])
    unused_cards = []
    # loops through all the answer cards and makes a list of all the possible answer cards that have not been used
    for index in range(max_a_cards):
        unused_cards.append(index + 1)
    # loops through the player ids and removes the answer cards taht are in the player's hand
    for ids in num_players:
        list_cards = cur.execute(f"SELECT ListCards FROM Players WHERE id = {ids}").fetchone()[0]
        list_cards = json.loads(list_cards)
        # loops through all the cards in the player with player id ids and removes the answer cards in their hand from the list
        for cards in list_cards:
            unused_cards.remove(cards)
            # checks to see if the current id is the players id and counts how many answer cards they currently have in their hand
            if (ids) == player_id:
                number_cards += 1
    list_cards = cur.execute(f"SELECT ListCards FROM Players WHERE id = {player_id}").fetchone()[0]
    list_cards = json.loads(list_cards)
    # loops until the player has the 7 cards in their hand and adds a random card into their hand
    for index in range(max_cards - number_cards):
        random_num = random.randint(1, len(unused_cards))
        # adds the random answer card id to the players hand
        list_cards.append(unused_cards[random_num])
        # removes the chosen answer card from the list of unused answer cards
        unused_cards.pop(random_num)
    cur.execute(f"UPDATE Players SET ListCards = '{list_cards}' WHERE id = {player_id}")
    # loops through all the answer card ids and turns them into the text equivilant to return it to the frontend
    for card_id in list_cards:
        acard = await answer_card(card_id)
        acard = acard["text"]
        temp_list.append(acard)
    list_cards = temp_list
    con.commit()
    # returns the list of answer card's text in the players hand
    return list_cards

@app.post("/create_game")
async def create_game():
    # creates a game in the db
    cur.execute(f"INSERT INTO Games (ListPlayerID, EveryoneIn) VALUES ('[]', False)")
    game_id = cur.lastrowid
    # gets a new question card and saves in the db
    q_card = await deal_qcard(game_id)
    con.commit()
    return game_id, q_card

@app.post("/everyone_in/{game_id}")
async def everyone_in(game_id: int):
    # sets the property EveryoneIn in the db to true
    cur.execute(f"UPDATE Games SET EveryoneIn = True WHERE id = {game_id}")
    con.commit()

@app.get("/check_EveryoneIn/{game_id}")
async def check_EveryoneIn(game_id: int):
    # checks if the property EveryoneIn in the db is true or false
    everyone_in = cur.execute(f"SELECT EveryoneIn FROM Games WHERE id = {game_id}").fetchone()[0]
    # booleans in a db are stored as 1 (true) or a 0 (false)
    if everyone_in == 0:
        everyone_in = False
    else:
        everyone_in = True
    return everyone_in

@app.post("/join_game/{game_id}/{player_id}")
async def join_game(player_id: int, game_id: int):
    # saves the players id into the list of players in the db
    # checks if there is no game in the db and if there isnt it creates a new one
    try:
        games = cur.execute(f"SELECT * FROM Games").fetchone()[0]
    except:
        game_id = await create_game()
        game_id = game_id[0]
    # saves the player's id into the list of players in the db
    list_players = cur.execute(f"SELECT ListPlayerID FROM Games WHERE id = {game_id}").fetchone()[0]
    list_players = json.loads(list_players)
    list_players.append(player_id)
    cur.execute(f"UPDATE Games SET ListPlayerID = '{list_players}' WHERE id = {game_id}")
    cur.execute(f"UPDATE Games SET CzarID = {player_id} WHERE id = {game_id}")
    con.commit()

@app.post("/save_choice/{player_id}/{choice}")
async def save_choice(player_id: int, choice: str):
    # saves the list of answer cards chosen by the player in the db
    choice = json.loads(choice)
    player_cards = cur.execute(f"SELECT ListCards FROM Players WHERE id = {player_id}").fetchone()[0]
    player_cards = json.loads(player_cards)
    choice_ids = []
    # loops thorugh the choices and gets their respective ids and saves it to a list
    for index in choice:
        choice_ids.append(player_cards[index - 1])
    # saves the list in the db
    cur.execute(f"UPDATE Players SET choice = '{choice_ids}' WHERE id = {player_id}")
    con.commit()

@app.post("/delete_game/{game_id}")
async def delete_game(game_id: int):
    # deletes the game with id game_id from the db
    cur.execute(f"DELETE FROM Games WHERE id = {game_id}")
    con.commit()

@app.post("/delete_player/{player_id}")
async def delete_player(player_id: int):
    # deletes the player with id player_id from the db
    cur.execute(f"DELETE FROM Players WHERE id = {player_id}")
    con.commit()

@app.get("/return_num_players/{game_id}")
async def return_num_players(game_id: int):
    # returns the number of players in the game
    list_player_id = cur.execute(f"SELECT ListPlayerID FROM Games WHERE id = {game_id}").fetchone()[0]
    list_player_id = json.loads(list_player_id)
    return len(list_player_id)

@app.get("/return_qcard/{game_id}")
async def return_qcard(game_id: int):
    # returns the question card from the db
    q_card_id = cur.execute(f"SELECT QCard FROM Games WHERE id = {game_id}").fetchone()[0]
    q_card = await question_card(q_card_id)
    num_gaps = q_card["num_gaps"]
    q_card = q_card["text"]
    return q_card, num_gaps

@app.get("/return_choices/{game_id}")
async def return_choices(game_id: int):
    # checks if all the players have submitted their answer cards and if they have it returns those choices
    choice_in = True
    list_choices = []
    list_players = cur.execute(f"SELECT ListPlayerID FROM Games WHERE id = {game_id}").fetchone()[0]
    list_players = json.loads(list_players)
    czar_id = cur.execute(f"SELECT CzarID FROM Games WHERE id = {game_id}").fetchone()[0]
    list_players.remove(czar_id)
    # loops through all the players and gets their answer cards
    for player_id in list_players:
        choice = cur.execute(f"SELECT choice FROM Players WHERE id = {player_id}").fetchone()[0]
        # tries to save the answer cards into a list and if it doesnt work it means that the player has not submitted their answer card
        try:
            choice = json.loads(choice)
            list_choices.append((player_id, choice))
        except:
            choice_in = False
            break
    # returns a false statement if the player has not submitted their answer card yet else it returns a true statement and the cards
    return choice_in, list_choices 

@app.post("/give_points/{czar_id}/{point_winner}")
async def give_points(czar_id: int, point_winner: int):
    # gives a point to the player who was chosen by the czar
    cur.execute(f"UPDATE Players SET choice = '{point_winner}' WHERE id = {czar_id}")
    points = cur.execute(f"SELECT points FROM Players WHERE id = {point_winner}").fetchone()[0]
    points += 1
    cur.execute(f"UPDATE Players SET points = '{points}' WHERE id = {point_winner}")
    con.commit()
    return points

@app.get("/return_czar_choice/{game_id}")
async def return_czar_choice(game_id: int):
    # checks if the player has submitted their choice and if they have it returns it
    choice_in = True
    czar_id = cur.execute(f"SELECT CzarID FROM Games WHERE id = {game_id}").fetchone()[0]
    czar_choice = cur.execute(f"SELECT choice FROM Players WHERE id = {czar_id}").fetchone()[0]
    # checks if the czar has chosen a set of cards
    # the empty choices can either be (NULL) or None
    if czar_choice == None or czar_choice == "(NULL)":
        choice_in = False
    return choice_in, czar_choice

@app.post("/reset_game/{game_id}")
async def reset_game(game_id: int):
    # this function will only be used in the admin page and it will reste the game so that the players can keep playing
    temp_list = []
    # resets the game in the database
    cur.execute(f"UPDATE Games SET ListPlayerID = '[]' WHERE id = {game_id}")
    cur.execute(f"UPDATE Games SET EveryoneIn = 0 WHERE id = {game_id}")
    await deal_qcard(game_id)
    # loops through all the player ids in the database and delets them
    # for now the code will delete all the players in the db, however, later if there are more than one game only the players of the game that is being reset mus tbe deleted
    # make list of the players and then delet them so that it does not stop deleting the players prematurely 
    for index in cur.execute(f"SELECT id FROM Players"):
        temp_list.append(index[0])
    for index in temp_list:
        await delete_player(index)
    con.commit()

@app.get("/admin")
async def admin():
    #returns the front end code for the admin page
    return HTMLResponse(open("admin.html", "rt").read())

@app.get("/")
async def root():
    #returns the front end code so that it can be run
    return HTMLResponse(open("CAH.html", "rt").read())
