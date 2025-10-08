from fastapi import FastAPI
import uvicorn

from get_tickets import get_some_id_info as tickets

app = FastAPI()

# 3855544
@app.get("/event/{event_id}")
def get_tickets(event_id):
    if type(event_id) is not (str, int):
        return "Данные должны быть строкой или числом"
    return tickets(event_id)

@app.get("/event/")
def get_tickets():
    return tickets()

if __name__ == '__main__':
    uvicorn.run(app, host="localhost", port=8000)