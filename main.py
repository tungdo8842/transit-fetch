from google.transit import gtfs_realtime_pb2
import requests
import csv
# from fastapi import FastAPI

class Bus_Route():
    def __init__(self, route_id, route_short_name, route_long_name, route_type, route_color, route_text_color):
        self.route_id = route_id
        self.route_short_name = route_short_name
        self.route_long_name = route_long_name
        self.route_type = route_type
        self.route_color = route_color
        self.route_text_color = route_text_color

    def __str__(self):
        return(f"route_id: {self.route_id}, route_short_name: {self.route_short_name}, route_long_name: {self.route_long_name}, " +
                f"route_type: {self.route_type}, route_color: {self.route_color}, route_text_color: {self.route_text_color}") 


# initialization
# app = FastAPI()

# fetch routh from static routes.txt
bus_routes = []
with open("./static_data/routes.txt", encoding="utf-8-sig") as file:
    reader = list(csv.DictReader(file))
    for route in reader:
        new_bus_route = Bus_Route(route["route_id"], route["route_short_name"], route["route_long_name"], \
                route["route_type"], route["route_color"], route["route_text_color"])
        bus_routes.append(new_bus_route)



feed = gtfs_realtime_pb2.FeedMessage()
response = requests.get("https://bct.tmix.se/gtfs-realtime/tripupdates.pb?operatorIds=48")

feed.ParseFromString(response.content)

# if not feed.entity:
#     print("Feed contained no entities")
# else:
for entity in feed.entity:
    if entity.HasField("trip_update"):
        trip = entity.trip_update.trip
        for route in bus_routes:
            if route.route_id == trip.route_id:
                print(f"Trip info: {route.route_short_name}: {route.route_long_name}, " +
                        f"Start time: {trip.start_time}")


# @app.get("/")
# async def root():
#     return {"message": ""}
