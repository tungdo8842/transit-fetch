from google.transit import gtfs_realtime_pb2
import requests
# from fastapi import FastAPI

# app = FastAPI()

feed = gtfs_realtime_pb2.FeedMessage()
response = requests.get("https://bct.tmix.se/gtfs-realtime/tripupdates.pb?operatorIds=48")

response.raise_for_status()

feed.ParseFromString(response.content)
if not feed.entity:
    print("Feed contained no entities")
else:
    for entity in feed.entity:
        if entity.HasField("trip_update"):
            print(entity.trip_update)

# @app.get("/placeholder")
# async def root():
#     return {"message": ""}
