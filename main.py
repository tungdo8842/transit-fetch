from google.transit import gtfs_realtime_pb2
from google.protobuf.json_format import MessageToDict
import requests
import csv, json
from collections import defaultdict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# CORS setup
origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BusRoute():
    def __init__(self, route_id, route_short_name, route_long_name, route_type, route_color, route_text_color):
        self.route_id = route_id
        self.route_short_name = route_short_name
        self.route_long_name = route_long_name
        self.route_type = route_type
        self.route_color = route_color
        self.route_text_color = route_text_color


class BusStop():
    def __init__(self, stop_id, stop_name, stop_lat, stop_lon, wheelchair_boarding, stop_code):
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.stop_lat = stop_lat
        self.stop_lon = stop_lon
        self.wheelchair_boarding = wheelchair_boarding
        self.stop_code = stop_code


class DepartureResponse():
    def __init__(self, stop_id, stop_name, route_id, route_short_name, route_long_name, route_color, time):
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.route_id = route_id
        self.route_short_name = route_short_name
        self.route_long_name = route_long_name
        self.route_color = route_color
        self.time = time

# initialization

# read static data
# keys are in str, not int
bus_routes = {}
bus_stops = {}

with open("./static_data/routes.txt", encoding="utf-8-sig") as file:
    reader = list(csv.DictReader(file))
    for route in reader:
        new_bus_route = BusRoute(route["route_id"], route["route_short_name"], route["route_long_name"], \
                route["route_type"], route["route_color"], route["route_text_color"])
        bus_routes[new_bus_route.route_id] = new_bus_route

with open("./static_data/stops.txt", encoding="utf-8-sig") as file:
    reader = list(csv.DictReader(file))
    for stop in reader:
        new_bus_stop = BusStop(stop["stop_id"], stop["stop_name"], stop["stop_lat"], stop["stop_lon"], \
                stop["wheelchair_boarding"], stop["stop_code"])
        bus_stops[new_bus_stop.stop_id] = new_bus_stop


feed = gtfs_realtime_pb2.FeedMessage()
response = requests.get("https://bct.tmix.se/gtfs-realtime/tripupdates.pb?operatorIds=48")

trips_per_stop = defaultdict(list)

feed.ParseFromString(response.content)

# Start converting dictionary object to message here
def get_trips_at_stops(feed, trips_per_stop):
    """sort all trips into a stop dictionary"""
    for entity in feed.entity:
        if entity.HasField("trip_update") and entity.trip_update.stop_time_update: # length != 0
            route_id = entity.trip_update.trip.route_id
            for update in entity.trip_update.stop_time_update:
                # filter out bad timestamp
                if update.departure.time == 0:
                    continue
                stop_id = update.stop_id
                trip = DepartureResponse(stop_id=stop_id, stop_name=bus_stops[stop_id].stop_name,
                                         route_id=route_id, route_short_name=bus_routes[route_id].route_short_name,
                                         route_long_name=bus_routes[route_id].route_long_name,
                                         route_color=bus_routes[route_id].route_color, time=update.departure.time)
                # add dictionary of trip class
                trips_per_stop[update.stop_id].append(trip.__dict__)


# TODO: complete the list
# A:9,4; B:14; C:15; M:39; R:26
uvic_bay_list = {"A": "101076", "B": "102416", "C": "102417", "M": "100741", "R": "100904"} # incomplete for now

get_trips_at_stops(feed, trips_per_stop)
# print(trips_per_stop)
uvic_trips = []

print("Uvic Bay C stop data:")
for stop_name in uvic_bay_list:
    uvic_trips.extend(trips_per_stop[uvic_bay_list[stop_name]])



@app.get("/bus/uvic-departures")
async def uvic_departures():
    return uvic_trips
