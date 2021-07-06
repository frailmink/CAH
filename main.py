from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sqlite3

con = sqlite3.connect('CAH.db') # connects to the database
cur = con.cursor() # creates a cursor

app = FastAPI()

@app.get("/answer_card/{card_id}")
async def answer_card(card_id):
    for card in cur.execute(f"SELECT * FROM AnswerCards WHERE id = {card_id}"):
        break
    return {
        "id": card[0],
        "text": card[1],
    }

@app.get("/question_card/{card_id}")
async def question_card(card_id):
    for card in cur.execute(f"SELECT * FROM QuestionCards WHERE id = {card_id}"):
        break
    return {
        "id": card[0],
        "text": card[1],
        "num_gaps": card[2]
    }

@app.get("/num_answer_cards")
async def question_card():
    for count in cur.execute("SELECT COUNT() FROM AnswerCards"):
        break
    return count[0]

@app.get("/num_question_cards")
async def question_card():
    for count in cur.execute("SELECT COUNT() FROM QuestionCards"):
        break
    return count[0]

@app.get("/")
async def root():
    return HTMLResponse(open("index.html", "rt").read())
