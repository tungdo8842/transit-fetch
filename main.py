from google.transit import gtfs_realtime_pb2
from google.protobuf.json_format import MessageToDict
import requests
import csv
from collections import defaultdict
from fastapi import FastAPI

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


class Bus_Stop():
    def __init__(self, stop_id, stop_name, stop_lat, stop_lon, wheelchair_boarding, stop_code):
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.stop_lat = stop_lat
        self.stop_lon = stop_lon
        self.wheelchair_boarding = wheelchair_boarding
        self.stop_code = stop_code

    def __str__(self):
        return (f"stop_id: {self.stop_id}, stop_name: {self.stop_name}, stop_lat: {self.stop_lat}, " +
                f"stop_lon: {self.stop_lon}, wheelchair_boarding: {self.wheelchair_boarding}, stop_code: {self.stop_code}")


# initialization
app = FastAPI()

# read static data
# keys are in str, not int
bus_routes = {}
bus_stops = {}

with open("./static_data/routes.txt", encoding="utf-8-sig") as file:
    reader = list(csv.DictReader(file))
    for route in reader:
        new_bus_route = Bus_Route(route["route_id"], route["route_short_name"], route["route_long_name"], \
                route["route_type"], route["route_color"], route["route_text_color"])
        bus_routes[new_bus_route.route_id] = new_bus_route

with open("./static_data/stops.txt", encoding="utf-8-sig") as file:
    reader = list(csv.DictReader(file))
    for stop in reader:
        new_bus_stop = Bus_Stop(stop["stop_id"], stop["stop_name"], stop["stop_lat"], stop["stop_lon"], \
                stop["wheelchair_boarding"], stop["stop_code"])
        bus_stops[new_bus_stop.stop_id] = new_bus_stop


feed = gtfs_realtime_pb2.FeedMessage()
response = requests.get("https://bct.tmix.se/gtfs-realtime/tripupdates.pb?operatorIds=48")

trips_per_stop = defaultdict(list)

feed.ParseFromString(response.content)

# def get_bus_at_stop(feed, stop_id:str):
#     depatures_list = []
#     for entity in feed.entity:
#         if entity.HasField("trip_update") and entity.trip_update.stop_time_update: # length != 0
#             for update in entity.trip_update.stop_time_update:
#                 if update.stop_id == stop_id:
#                     depatures_list.append(update)
#     return depatures_list

# Start converting dictionary object to message here
def get_trips_at_stops(feed, trips_per_stop):
    """sort all trips into a stop dictionary"""
    for entity in feed.entity:
        if entity.HasField("trip_update") and entity.trip_update.stop_time_update: # length != 0
            for update in entity.trip_update.stop_time_update:
                trips_per_stop[update.stop_id].append(MessageToDict(update))

# TODO: complete the list
# A:9,4; B:14; C:15; M:39; R:26
uvic_bay_list = {"A": "101076", "B": "102416", "C": "102417", "M": "100741", "R": "100904"} # incomplete for now

get_trips_at_stops(feed, trips_per_stop)
# print(trips_per_stop)
uvic_trips = []

print("Uvic Bay C stop data:")
for stop_name in uvic_bay_list:
    uvic_trips.extend(trips_per_stop[uvic_bay_list[stop_name]])

# print(uvic_trips)


# @app.get("/")
# async def root():
#     return {"message": ""}

@app.get("/bus/uvic_depatures")
async def uvic_depatures():
    return uvic_trips
