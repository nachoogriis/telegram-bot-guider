# NEEDED LIBRARIES #
from tkinter import *
from dataclasses import dataclass
from typing import Optional, TextIO
import pandas as pd  # type: ignore
from typing import List, Tuple
import networkx as nx  # type: ignore
from haversine import haversine  # type: ignore
from staticmap import StaticMap, CircleMarker, Line  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import matplotlib.colors as mcolors  # type: ignore
from typing_extensions import TypeAlias
import matplotlib
matplotlib.use('WebAgg')

MetroGraph: TypeAlias = nx.Graph
Coord: TypeAlias = Tuple[float, float]

# STATION CLASS #


@dataclass
class Station:

    # STATION CLASS ATTRIBUTES #

    station_line_id: int
    station_id: int
    station_name: str
    station_order: int
    line_name: str
    line_origin: str
    line_end: str
    accessibility: str
    state: str
    line_color: str
    latitude: float
    longitude: float


# ACCESS CLASS #

@dataclass
class Access:

    # ACCESS CLASS ATTRIBUTES #

    access_id: int
    access_name: str
    conn_station_id: int
    station_name: str
    accessibility: str
    latitude: float
    longitude: float


Stations: TypeAlias = List[Station]

Accesses: TypeAlias = List[Access]


def station_position(station: Station) -> Coord:
    """ Return the latitude and longitude of a station as a Tuple """
    lat: float = station.latitude
    lon: float = station.longitude

    return (lat, lon)


def access_position(access: Access) -> Coord:
    """ Return the latitude and longitude of a station as a Tuple """
    lat: float = access.latitude
    lon: float = access.longitude

    return (lat, lon)


def read_stations() -> Stations:
    """ Llegeix un fitxer .csv amb la informació corresponent a les estacions i
    retorna una llista amb tots els atributs importants de cada estació """

    # Columns used from the ones in the url file
    used_columns: List = ["CODI_ESTACIO_LINIA", "CODI_ESTACIO", "NOM_ESTACIO",
                          "ORDRE_ESTACIO", "NOM_LINIA", "ORIGEN_SERVEI",
                          "DESTI_SERVEI", "NOM_TIPUS_ACCESSIBILITAT",
                          "NOM_TIPUS_ESTAT", "COLOR_LINIA", "GEOMETRY"]

    # Specified data types for each column / attribute
    column_types: dict = {
        "CODI_ESTACIO_LINIA": int,
        "CODI_ESTACIO": int,  # Mirar si es lo mismo siempre para ID_ESTACIO
        "NOM_ESTACIO": str,
        "ORDRE_ESTACIO": int,
        "NOM_LINIA": str,
        "ORIGEN_SERVEI": str,
        "DESTI_SERVEI": str,
        "NOM_TIPUS_ACCESSIBILITAT": str,
        "NOM_TIPUS_ESTAT": str,
        "COLOR_LINIA": str,
        "GEOMETRY": str
    }

    # We read the csv file and save it's data as a pandas data frame
    df = pd.read_csv("estacions.csv", usecols=used_columns,
                     dtype=column_types, keep_default_na=False,
                     encoding='latin1')

    # List where all stations will be stored
    stations_list: Stations = []

    # We iterate through each "station" to save it's data as an object (Station
    # object)
    for row in df.itertuples():
        # From the geometry column we obtain longitude and latitude
        list_coordinates: List = row.GEOMETRY[7:-1].split(" ")

        lat: float = float(list_coordinates[0])
        lon: float = float(list_coordinates[1])

        # We create the station and add it to the stations list
        s: Station = Station(row.CODI_ESTACIO_LINIA, row.CODI_ESTACIO,
                             row.NOM_ESTACIO, row.ORDRE_ESTACIO, row.NOM_LINIA,
                             row.ORIGEN_SERVEI, row.DESTI_SERVEI,
                             row.NOM_TIPUS_ACCESSIBILITAT, row.NOM_TIPUS_ESTAT,
                             row.COLOR_LINIA,  lat, lon)
        stations_list.append(s)

    return stations_list


def read_accesses() -> Accesses:
    """ Llegeix un fitxer .csv amb la informació corresponent als accessos i
    retorna una llista amb tots els atributs importants de cada accés """

    # Columns used from the ones in the url file
    used_columns: List = ["CODI_ACCES", "NOM_ACCES", "ID_ESTACIO",
                          "NOM_ESTACIO", "NOM_TIPUS_ACCESSIBILITAT",
                          "GEOMETRY"]

    # Specified data types for each column / attribute
    column_types: dict = {
        "CODI_ACCES": int,
        "NOM_ACCES": str,
        "ID_ESTACIO": int,
        "NOM_ESTACIO": str,
        "NOM_TIPUS_ACCESSIBILITAT": str,
        "GEOMETRY": str
    }

    df = pd.read_csv("accessos.csv", usecols=used_columns,
                     dtype=column_types, keep_default_na=False,
                     encoding='latin1')

    accesses_list: Accesses = []

    # We iterate through each "access" to save it's data as an object (Access
    # object)
    for row in df.itertuples():
        # From the geometry column we obtain longitude and latitude
        list_coordinates: List = row.GEOMETRY[7:-1].split(" ")

        lat: float = float(list_coordinates[0])
        lon: float = float(list_coordinates[1])

        # We create the access and add it to the accesses list
        a: Access = Access(row.CODI_ACCES, row.NOM_ACCES, row.ID_ESTACIO,
                           row.NOM_ESTACIO, row.NOM_TIPUS_ACCESSIBILITAT,
                           lat, lon)
        accesses_list.append(a)

    return accesses_list


def add_edge_tram(metro: MetroGraph, act_station: Station,
                  prev_station: Station) -> None:
    """ Adds an edge (of "Tram" type) between the two given stations with all
    attributes needed """
    # We create a dictionary with all the attributes of the edge
    info_edge: dict = {
        "tipus": "Tram",
        "linia": act_station.line_name,
        "distancia": haversine(station_position(prev_station),
                               station_position(act_station)),
        "color": "#" + act_station.line_color,
        "start": station_position(act_station),
        "end": station_position(prev_station)
    }
    metro.add_edge(act_station.station_line_id, prev_station.station_line_id,
                   edge_attributes=info_edge)


def add_edge_link(metro: MetroGraph, node: Station,
                  act_station: Station) -> None:
    """ Adds an edge (of link type) between the two given station with all the
    attributes needed """
    info_station: Station = metro.nodes[node]['attributes']
    # We create a dictionary with all the attributes of the edge
    info_edge: dict = {
        "tipus": "Enllaç",
        "distancia": haversine(station_position(info_station),
                               station_position(act_station)),
        "color": "#ffc0cb",
        "start": station_position(act_station),
        "end": station_position(info_station)
    }
    metro.add_edge(node, act_station.station_line_id,
                   edge_attributes=info_edge)


def add_edge_access(metro: MetroGraph, station: Station,
                    act_access: Access) -> None:
    """ Adds an edge (of access type) between the given station and access with
    all the attribues needed """
    info_edge: dict = {
        "tipus": "Acces",
        "distancia": haversine(station_position(station),
                               access_position(act_access)),
        "color": "#000000",
        "start": access_position(act_access),
        "end": station_position(station)
    }
    metro.add_edge(station.station_line_id, act_access.access_id,
                   edge_attributes=info_edge)


def add_stations(metro: MetroGraph, stations_list: Stations) -> None:
    """ Adds all the stations to the graph as nodes and, at the same time, the
    edges beteween stations """
    # Prev stands for previous and act for actual. First, there is no prev_line
    prev_line: str = ""
    prev_station: Station = stations_list[0]
    for act_station in stations_list:
        # We update the actual line and add the node to the graph
        act_line = act_station.line_name
        metro.add_node(act_station.station_line_id, attributes=act_station,
                       pos=station_position(act_station), type="station")

        # As the stations are given in order, if they are from the same line we
        # need to add an edge between the actual station and the one checked
        # before
        if prev_line == act_line:
            add_edge_tram(metro, act_station, prev_station)

        # We update the parameters
        prev_station = act_station
        prev_line = act_station.line_name

        for node in metro.nodes():
            info_station = metro.nodes[node]['attributes']
            if (info_station.station_name == act_station.station_name
               and act_station.station_line_id != node):
                add_edge_link(metro, node, act_station)


def add_accesses(metro: MetroGraph, accesses_list: Accesses,
                 stations_list: Stations, special_acess: bool) -> None:
    """ Adds all the stations to the graph as nodes and, at the same time, the
    edges beteween stations and accesses """

    for act_access in accesses_list:
        if special_acess:
            if act_access.accessibility == "Accessible":
                metro.add_node(act_access.access_id, attributes=act_access,
                               pos=access_position(act_access), type="access")
                for station in stations_list:
                    if station.station_id == act_access.conn_station_id:
                        add_edge_access(metro, station, act_access)
                        break
        else:
            metro.add_node(act_access.access_id, attributes=act_access,
                           pos=access_position(act_access), type="access")
            for station in stations_list:
                if station.station_id == act_access.conn_station_id:
                    add_edge_access(metro, station, act_access)
                    break


def get_metro_graph(special_access: bool) -> MetroGraph:
    """ Genera i retorna el graf del metro amb les estacions, els accessos i
    les arestes que els connecten """
    metro: MetroGraph = nx.Graph()

    stations_list: Stations = read_stations()
    add_stations(metro, stations_list)

    accesses_list: Accesses = read_accesses()
    add_accesses(metro, accesses_list, stations_list, special_access)

    return metro


def show(g: MetroGraph) -> None:
    """ Mostra el graf obtingut amb la funció get_metro_graph a una
    finestra """
    options: dict = {
        'node_size': 7,
        'width': 1
    }
    # We get the list with all node positions on the graph
    pos = nx.get_node_attributes(g, 'pos')
    nx.draw(g, pos, **options)
    plt.draw()
    plt.show()
    plt.savefig("metro_graph.png")


def add_edges(mapa: StaticMap, g: MetroGraph) -> StaticMap:
    """ Adds edges to the metro map """
    for edge in g.edges():
        origin_id = int(edge[0])
        dest_id = int(edge[1])
        c1 = g.edges[edge]["edge_attributes"]["start"]
        c2 = g.edges[edge]["edge_attributes"]["end"]
        color = g.edges[edge]["edge_attributes"]["color"]
        mapa.add_line(Line((c1, c2), color, 5))
    return mapa


def add_nodes(mapa: StaticMap, g: MetroGraph) -> StaticMap:
    """ Adds nodes to the metro map """
    for node in g.nodes():
        marker = CircleMarker((g.nodes[node]["attributes"]._latitude,
                               g.nodes[node]["attributes"]._longitude),
                              "black", 8)
        mapa.add_marker(marker)

    return mapa


def plot(g: MetroGraph, filename: str) -> None:
    """ Desa el graf obingut amb la funció get_metro_graph com una imatge amb
    el mapa de la ciutat de fons en l'arxiu especificat a <filename> """
    # We create the map with the desired dimensions
    metro_map = StaticMap(2500, 3000, 50)

    # We add the edges and the nodes of the graph
    metro_map = add_edges(metro_map, g)
    metro_map = add_nodes(metro_map, g)

    # Now we create the image and save it
    image = metro_map.render()
    image.save(filename)


def main():
    # We generate the graph
    g1 = get_metro_graph(False)
    print("The number of nodes is: {}".format(g1.number_of_nodes()))
    print("The number of edges is: {}".format(g1.number_of_edges()))

    g2 = get_metro_graph(True)
    print("The number of nodes is: {}".format(g2.number_of_nodes()))
    print("The number of edges is: {}".format(g2.number_of_edges()))
    # We show the metro graph and plot it in a map of barcelona
    show(g1)
    show(g2)
    # plot(g, "metro_map.png")


# main()
