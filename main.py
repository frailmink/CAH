from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sqlite3

con = sqlite3.connect('CAH.db') # connects to the database
cur = con.cursor() # creates a cursor

app = FastAPI()

@app.get("/card/{card_id}")
async def card(card_id):
    for card in cur.execute(f"SELECT * FROM Cards WHERE id = {card_id}"):
        break
    return {
        "id": card[0],
        "type": card[1],
        "text": card[2],
        "NumGaps": card[3]
    }

@app.get("/")
async def root():
    return HTMLResponse(open("index.html", "rt").read())
