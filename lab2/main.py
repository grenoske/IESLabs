from datetime import datetime
from fastapi import FastAPI, WebSocketDisconnect, WebSocket, HTTPException
from pydantic import BaseModel, validator
from config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
from sqlalchemy import Table, Column, Integer, String, Float, DateTime, create_engine, MetaData, inspect
from sqlalchemy.exc import SQLAlchemyError
import json
from typing import List, Set

DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_engine(DATABASE_URL)
metadata = MetaData()
user_id_my = 1

# Define the ProcessedAgentData table
processed_agent_data = Table(
    "processed_agent_data",metadata,
    Column("user_id", Integer),
    Column("id", Integer, primary_key=True, index=True), 
    Column("road_state", String),
    Column("x", Float),
    Column("y", Float),
    Column("z", Float),
    Column("latitude", Float), 
    Column("longitude", Float), 
    Column("timestamp", DateTime),
)


# FastAPI models
class AccelerometerData(BaseModel): 
    x: float
    y: float
    z: float


class GpsData(BaseModel): 
    latitude: float
    longitude: float

class AgentData(BaseModel):
    user_id: int
    accelerometer: AccelerometerData
    gps: GpsData
    timestamp: datetime

    @validator('timestamp') 
    def check_timestamp(cls, value):
        if not isinstance(value, datetime):
            raise ValueError("Timestamp must be a datetime object")
        return value


class  ProcessedAgentData(BaseModel):
    road_state: str
    agent_data: AgentData

class ProcessedAgentDataInDB(BaseModel):
    id: int
    user_id: int
    road_state: str 
    x: float
    y: float 
    z: float
    latitude: float 
    longitude: float 
    timestamp: datetime


app = FastAPI()
subscriptions: Set[WebSocket] = set()
# FastAPI WebSocket endpoint
@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    subscriptions.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        subscriptions.remove(websocket)
# Function to send data to subscribed users
async def send_data_to_subscribers(data):
    for websocket in subscriptions:
        await websocket.send_json(data)



#   --- DATABASE ---
# Database interactions
def insert_processed_agent_data_to_db(data: ProcessedAgentData):
    try:
        with engine.connect() as conn:
            inserted = conn.execute(processed_agent_data.insert().values(
                user_id = user_id_my,          
                road_state=data.road_state,
                x=data.agent_data.accelerometer.x,
                y=data.agent_data.accelerometer.y,
                z=data.agent_data.accelerometer.z,
                latitude=data.agent_data.gps.latitude,
                longitude=data.agent_data.gps.longitude,
                timestamp=data.agent_data.timestamp
            ))
            conn.commit()
            return inserted.inserted_primary_key[0]
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        return None

def get_processed_agent_data_from_db(processed_agent_data_id: int):
    with engine.connect() as conn:
        result = conn.execute(processed_agent_data.select().where(processed_agent_data.c.id == processed_agent_data_id)).fetchone()
        if result:
            columns = processed_agent_data.columns.keys()
            result_dict = dict(zip(columns, result))
            return result_dict
        else:
            return None

def get_all_processed_agent_data_from_db():
    list_result = []
    with engine.connect() as conn:
        result = conn.execute(processed_agent_data.select()).fetchall()
        print(result)
        if result:
            columns = processed_agent_data.columns.keys()
            for col in result:
                result_dict = dict(zip(columns, col))
                list_result.append(result_dict)

    return list_result

def update_processed_agent_data_in_db(processed_agent_data_id: int, data: ProcessedAgentData):
    with engine.connect() as conn:
        conn.execute(processed_agent_data.update().where(processed_agent_data.c.id == processed_agent_data_id).values(
            user_id = user_id_my,
            road_state=data.road_state,
            x=data.agent_data.accelerometer.x,
            y=data.agent_data.accelerometer.y,
            z=data.agent_data.accelerometer.z,
            latitude=data.agent_data.gps.latitude,
            longitude=data.agent_data.gps.longitude,
            timestamp=data.agent_data.timestamp
        ))
        conn.commit()
        return get_processed_agent_data_from_db(processed_agent_data_id)

def delete_processed_agent_data_from_db(processed_agent_data_id: int):
    with engine.connect() as conn:
        deleted = conn.execute(processed_agent_data.delete().where(processed_agent_data.c.id == processed_agent_data_id))
        conn.commit()
        return deleted.rowcount > 0



# FastAPI CRUDL endpoints
@app.post("/processed_agent_data/")
async def create_processed_agent_data(data:List[ProcessedAgentData]):
    # Insert data to database
    inserted_data = []
    for item in data:
        inserted = insert_processed_agent_data_to_db(item)
        if inserted is None:
            raise HTTPException(status_code=500, detail="Failed to insert data into database")
        inserted_data.append(get_processed_agent_data_from_db(inserted))
    
    # Send data to subscribers
    await send_data_to_subscribers(inserted_data)
    return inserted_data
    
@app.get(
    "/processed_agent_data/{processed_agent_data_id}",
    response_model=ProcessedAgentDataInDB
)
def read_processed_agent_data(processed_agent_data_id: int):
    # Get data by id
    data = get_processed_agent_data_from_db(processed_agent_data_id)
    if not data:
        raise HTTPException(status_code=404, detail="Data not found")
    return data

@app.get(
    "/processed_agent_data/",
    response_model=list[ProcessedAgentDataInDB]
)
def list_processed_agent_data():
    # Get list of data
    data = get_all_processed_agent_data_from_db()
    return data

@app.put(
    "/processed_agent_data/{processed_agent_data_id}",
    response_model=ProcessedAgentDataInDB
)
def update_processed_agent_data(
    processed_agent_data_id: int,
    data: ProcessedAgentData
):
    # Update data
    updated_data = update_processed_agent_data_in_db(processed_agent_data_id, data)
    if not updated_data:
        raise HTTPException(status_code=404, detail="Data not found")
    send_data_to_subscribers(updated_data)
    return updated_data

@app.delete(
    "/processed_agent_data/{processed_agent_data_id}",
    response_model=ProcessedAgentDataInDB
)
def delete_processed_agent_data(processed_agent_data_id: int):
    data = get_processed_agent_data_from_db(processed_agent_data_id)
    if not data:
        raise HTTPException(status_code=404, detail="Data not found")
    
    # Delete by id
    delete_processed_agent_data_from_db(processed_agent_data_id)
    return data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)