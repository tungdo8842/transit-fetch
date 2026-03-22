from google.transit import gtfs_realtime_pb2
import requests
import csv
from collections import defaultdict
from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# Data classes
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


class BusTrip():
    def __init__(self, route_id, service_id, trip_id, trip_headsign, shape_id, block_id, direction_id):
        self.route_id = route_id
        self.service_id = service_id
        self.trip_id = trip_id
        self.trip_headsign = trip_headsign
        self.shape_id = shape_id
        self.block_id = block_id
        self.direction_id = direction_id


class DepartureResponse():
    def __init__(self, stop_id, stop_name, route_id, route_short_name, trip_headsign, route_color, time):
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.route_id = route_id
        self.route_short_name = route_short_name
        self.trip_headsign = trip_headsign
        self.route_color = route_color
        self.time = time


# read static data
# keys are in str, not int
bus_routes = {}
bus_stops = {}
bus_trips = {}

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

with open("./static_data/trips.txt", encoding="utf-8-sig") as file:
    reader = list(csv.DictReader(file))
    for trip in reader:
        new_bus_trip = BusTrip(trip["route_id"], trip["service_id"], trip["trip_id"], trip["trip_headsign"], \
                trip["shape_id"], trip["block_id"], trip["direction_id"])
        bus_trips[new_bus_trip.trip_id] = new_bus_trip

# Feed data processing
def get_trips_at_stops(feed):
    """sort all trips into a stop dictionary"""
    trips_per_stop = defaultdict(list)

    for entity in feed.entity:
        if entity.HasField("trip_update") and entity.trip_update.stop_time_update: # length != 0
            route_id = entity.trip_update.trip.route_id
            trip_id = entity.trip_update.trip.trip_id

            for update in entity.trip_update.stop_time_update:
                # filter out bad timestamp
                if update.departure.time == 0:
                    continue
                stop_id = update.stop_id

                try:
                    trip = DepartureResponse(stop_id=stop_id, stop_name=bus_stops[stop_id].stop_name,
                                             route_id=route_id, route_short_name=bus_routes[route_id].route_short_name,
                                             trip_headsign=bus_trips[trip_id].trip_headsign,
                                             route_color=bus_routes[route_id].route_color, time=update.departure.time)
                    # use dictionary of DepartureResponse class for api response
                    trips_per_stop[update.stop_id].append(trip.__dict__)
                except:
                    # TODO: on error, update static data or ignore certain error
                    continue

    return trips_per_stop


def get_uvic_bus(uvic_bay_list, trips_per_stop):
    uvic_trips = []
    for stop_name in uvic_bay_list:
        uvic_trips.extend(trips_per_stop[uvic_bay_list[stop_name]])

    uvic_trips.sort(key=lambda d: d["time"])

    return uvic_trips


# Periodically updating data
async def update_feed_data(app):
    while True:
        # GTFS Feed requests
        try:
            response = requests.get("https://bct.tmix.se/gtfs-realtime/tripupdates.pb?operatorIds=48")
            app.state.feed.ParseFromString(response.content)
        except:
            await asyncio.sleep(10)
            continue

        # put all trips into their associated stop
        app.state.trips_per_stop = get_trips_at_stops(app.state.feed)
        # # A:4/9, B:14, C:15, G:7, M:39, R:26 (incomplete list)
        app.state.uvic_bay_list = {"A": "101076", "B": "102416", "C": "102417", "G": "100405","M": "100741", "R": "100904"}
        app.state.uvic_trips = get_uvic_bus(app.state.uvic_bay_list, app.state.trips_per_stop)
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app):
    app.state.feed = gtfs_realtime_pb2.FeedMessage()
    asyncio.create_task(update_feed_data(app))
    yield


app = FastAPI(lifespan=lifespan)


# CORS setup
origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:3000",
    "https://tungdo.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/bus/uvic-departures")
async def uvic_departures():
    return app.state.uvic_trips
