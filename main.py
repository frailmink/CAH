# run this with uvicorn app:main and go to http://localhost:8000
# for testing go to http://localhost:8000/docs

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sqlite3

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

@app.get("/")
async def root():
    #returns the front end code so that it can be run
    return HTMLResponse(open("index.html", "rt").read())
