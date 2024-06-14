# NEEDED LIBRARIES #
from dataclasses import dataclass
from typing import Optional, TextIO
from typing import List, Tuple, Union
import networkx as nx  # type: ignore
from haversine import haversine  # type: ignore
from staticmap import StaticMap, CircleMarker, Line  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import matplotlib.colors as mcolors  # type: ignore
from typing_extensions import TypeAlias
import osmnx as ox  # type: ignore
import os
import pickle
import math
# LOCAL LIBRARIES #
import metro
# TO SHOW THE PLOT #
import matplotlib as mlt
mlt.use('WebAgg')

CityGraph: TypeAlias = nx.Graph
MetroGraph: TypeAlias = nx.Graph
OsmnxGraph: TypeAlias = nx.MultiDiGraph
Coord: TypeAlias = Tuple[float, float]  # (latitude, longitude)
NodeID: TypeAlias = Union[int, str]
Path: TypeAlias = List[NodeID]


@dataclass
class Edge:
    type: str
    color: str
    distance: float
    start: Coord
    end: Coord


def load_osmnx_graph(filename: str) -> OsmnxGraph:
    """ Reads the file to create in a more efficient way the graph """
    in_f = open(filename, "rb")
    g: OsmnxGraph = pickle.load(in_f)
    in_f.close()
    return g


def save_osmnx_graph(g: OsmnxGraph, filename: str) -> None:
    """ Saves the given graph in a _.txt file using pickle """
    out_f = open(filename, "wb")
    pickle.dump(g, out_f)
    out_f.close()


def get_osmnx_graph() -> OsmnxGraph:
    """ Returns Barcelona's streets graph using OSMnx """
    filename: str = "street_graph_bcn.dat"
    g: OsmnxGraph
    if os.path.exists(filename):
        # We read the graph from the file using Pickle
        g = load_osmnx_graph(filename)
    else:
        # We obtain the graph with OSMnx
        g = ox.graph_from_place("Barcelona", network_type='walk',
                                simplify=True)
        # We save it using Pickle
        save_osmnx_graph(g, filename)
    return g


def speed_by_type(type: str) -> float:
    """ Returns the average speed of an edge in m/s """
    if type == "Tram":
        return 30
    return 6


def add_g2_graph(g: CityGraph, g2: MetroGraph) -> None:
    """ Adds all the nodes and edges from g2 to g """
    for node in list(g2.nodes):
        g.add_node(node, attributes=g2.nodes[node]["attributes"],
                   pos=g2.nodes[node]["pos"], type=g2.nodes[node]["type"],
                   color="#000000")

    for edge in list(g2.edges):
        # We get all the attributes needed to initialize an Edge (class)
        eattr: dict = g2.edges[edge]["edge_attributes"]
        type: str = eattr["tipus"]
        color: str = eattr["color"]
        distance: float = eattr["distancia"]
        start: Coord = eattr["start"]
        end: Coord = eattr["end"]
        speed: float = speed_by_type(type)

        time: float = distance / speed * 60
        # Documentar retards
        if type == "Enllaç":
            time += 3

        # We initialize an Edge object
        e: Edge = Edge(type, color, distance, start, end)
        # We create the edge with its information given as an Edge object
        g.add_edge(edge[0], edge[1], info=e, weight=time)


def add_g1_graph(g: CityGraph, g1: OsmnxGraph) -> None:
    """ Adds all the nodes and edges from g1 to g """
    for node in list(g1.nodes):
        g.add_node(node, pos=(g1.nodes[node]["x"], g1.nodes[node]["y"]),
                   type="street", color="#0E800B")

    for u, nbrsdict in g1.adjacency():
        for v, edgesdict in nbrsdict.items():
            eattr = edgesdict[0]
            if 'geometry' in eattr:
                del(eattr['geometry'])

            if u != v:
                type: str = "street"
                color: str = "#F4F410"
                start: Coord = (g1.nodes[u]["x"], g1.nodes[u]["y"])
                end: Coord = (g1.nodes[v]["x"], g1.nodes[v]["y"])
                distance: float = haversine(start, end)
                speed: float = speed_by_type(type)

                time: float = distance / speed * 60
                # We initialize an Edge object
                e: Edge = Edge(type, color, distance, start, end)
                # We create the edge with its information given as an Edge
                g.add_edge(u, v, info=e, weight=time)


def get_closest_street(node: NodeID, g2: MetroGraph,
                       g1: OsmnxGraph) -> NodeID:
    """ Returns the id of the street node which is closest to the given access
    """
    min_dist: float = -1
    final_street: NodeID = -1
    # We declare the access from which we want to find the closest street node
    access: metro.Access = g2.nodes[node]["attributes"]

    # We iterate through all the street nodes
    for street in list(g1.nodes):
        dist = haversine((metro.access_position(access)),
                         (g1.nodes[street]["x"],
                          g1.nodes[street]["y"]), unit="m")

        # If the distance from the access to the street node is smaller than
        # the minimum distance found, we update the parameters. We also update
        # the parameters when we are in the first iteration
        if min_dist == -1 or dist <= min_dist:
            min_dist = dist
            final_street = street

    return final_street


def add_remaining_edges(g: CityGraph, g1: OsmnxGraph, g2: MetroGraph) -> None:
    """ Adds the remaining edges to g. This means edges that go from one
    access from it's closest street node """
    for node in list(g2.nodes):
        if g2.nodes[node]["type"] == "access":
            # We get the closes street node to the access
            street: NodeID = get_closest_street(node, g2, g1)

            # We get all the attributes needed to initialize an Edge (class)
            type: str = "street"
            color: str = "#FDA702"
            start_node: metro.Access = g2.nodes[node]["attributes"]
            end_node = g1.nodes[street]
            start: Coord = (metro.access_position(start_node))
            end: Coord = (end_node["x"], end_node["y"])
            distance: float = haversine(start, end)
            speed: float = speed_by_type(type)

            time: float = distance / speed * 60
            # We initialize an Edge object
            e: Edge = Edge(type, color, distance, start, end)
            # We create the edge with its information given as an Edge object
            g.add_edge(node, street, info=e, weight=time)


def build_city_graph(g1: OsmnxGraph, g2: MetroGraph) -> CityGraph:
    """ Returns de city graph. A fusion between the metro graph and the streets
    graph """
    g: CityGraph = nx.Graph()

    # First we add the nodes and edges from the metro graph
    add_g2_graph(g, g2)
    # Now we add the nodes and edges from the street graph
    add_g1_graph(g, g1)
    # We add all the edges that go from accesses to their closest street node
    add_remaining_edges(g, g1, g2)

    return g


def load_city_graph(filename: str) -> CityGraph:
    """ Reads the filename.txt file to create in a more efficient way the graph
    """
    in_f = open(filename, "rb")
    g: OsmnxGraph = pickle.load(in_f)
    in_f.close()
    return g


def save_city_graph(g: CityGraph, filename: str) -> None:
    """ Saves the given graph in a _.txt file using pickle """
    out_f = open(filename, "wb")
    pickle.dump(g, out_f)
    out_f.close()


def get_city_graph(special_access: bool) -> CityGraph:
    """ Returns Barcelona's city graph (union of metro and streets). The
    bool varible is used to know if special accessibility is needed. """
    filename: str = "city_graph_bcn.dat"
    if special_access:
        filename = "special_access_city_graph_bcn.dat"
    g: CityGraph
    if os.path.exists(filename):
        # We read the graph from the file using Pickle
        g = load_city_graph(filename)
    else:
        # We create the city graph
        g1: OsmnxGraph = get_osmnx_graph()
        g2: MetroGraph = metro.get_metro_graph(special_access)
        g = build_city_graph(g1, g2)

        # We save it using Pickle
        save_city_graph(g, filename)
    return g


def get_closest_node(ox_g: OsmnxGraph, pos: Coord) -> NodeID:
    """ Returns the closest street node to the given position """
    min_dist: float = -1
    final_node: NodeID = -1

    # CAMBIAR ESTO PARA UTILIZAR LA FUNCIÓN DE NX

    # We iterate through all the street nodes
    for node in list(ox_g.nodes):
        dist = haversine((pos[0], pos[1]), (ox_g.nodes[node]["x"],
                                            ox_g.nodes[node]["y"]))
        # If the distance from the access to the street node is smaller than
        # the minimum distance found, we update the parameters. We also update
        # the parameters when we are in the first iteration
        if min_dist == -1 or dist < min_dist:
            min_dist = dist
            final_node = node

    return final_node


def find_path(ox_g: OsmnxGraph, g: CityGraph, src: Coord, dst: Coord) -> Path:
    """ Returns the min path from src to dst in g """
    # We get the closest street to the given positions
    src_node: NodeID = get_closest_node(ox_g, src)
    dst_node: NodeID = get_closest_node(ox_g, dst)

    path: Path = nx.dijkstra_path(g, src_node, dst_node, weight="weight")

    return path


def travel_time(path: Path, g: CityGraph) -> int:
    """ Returns the total travel time, rounded as integer, of a given path """
    total_time: int = 0

    for i in range(1, len(path)):
        total_time += g.edges[path[i-1], path[i]]["weight"]

    return int(round(total_time, 0))


def plot_path(g: CityGraph, p: Path, filename: str) -> None:
    """ Shows the toute p in <filename> file """
    path_map = StaticMap(750, 750)

    time: float = 0
    previous: NodeID
    for node in p:
        if node == p[0] or node == p[-1] or g.nodes[node]["type"] != "street":
            marker = CircleMarker(g.nodes[node]["pos"], "black", 5)
            path_map.add_marker(marker)

        if node != p[0]:
            time += (g[previous][node]["weight"])
            if g[previous][node]["info"].type == "Enllaç":
                time += 3
            c1: Coord = g[previous][node]["info"].start
            c2: Coord = g[previous][node]["info"].end
            color: str = "#000000"
            if g[previous][node]["info"].type != "street":
                color = g[previous][node]["info"].color
            path_map.add_line(Line((c1, c2), color, 3))

        previous = node
    print("Aproximated travel time: {}".format(int(time)))
    image = path_map.render()
    image.save(filename)


def show(g: CityGraph) -> None:
    """ Shows g in a window in an interactive way """
    options = {
        'node_size': 7,
        'width': 1
    }
    pos: Coord = nx.get_node_attributes(g, 'pos')
    nx.draw(g, pos,  **options)
    plt.draw()
    plt.show()
    plt.savefig("city_graph.png")


def add_edges(city_map: StaticMap, g: CityGraph) -> StaticMap:
    """ Adds edges to the city map """
    for edge in g.edges():
        origin_id: NodeID = int(edge[0])
        dest_id: NodeID = int(edge[1])
        c1: Coord = g.edges[edge]["info"].start
        c2: Coord = g.edges[edge]["info"].end
        color = g.edges[edge]["info"].color
        city_map.add_line(Line((c1, c2), color, 5))
    return city_map


def add_nodes(city_map: StaticMap, g: CityGraph) -> StaticMap:
    """ Adds nodes to the city map """
    for node in list(g.nodes):
        marker = CircleMarker(g.nodes[node]["pos"], g.nodes[node]["color"], 7)
        city_map.add_marker(marker)

    return city_map


def plot(g: CityGraph, filename: str) -> None:
    """ Saves g as an image with Barcelona's map as background in <filename>
    file """
    # We create the map with the desired dimensions
    city_map = StaticMap(750, 750)

    # We add the edges and the nodes of the graph
    city_map = add_edges(city_map, g)
    city_map = add_nodes(city_map, g)

    # Now we create the image and save it
    image = city_map.render()
    image.save(filename)

# --------------------- CODE FOR DOING TESTS --------------------- #

# ox_g = get_osmnx_graph()
# g = get_city_graph()
# print("The number of nodes is: {}".format(g.number_of_nodes()))
# print("The number of edges is: {}".format(g.number_of_edges()))
#
# src = (2.113292312485838, 41.38823386356948)
# dst = (2.1900245574485586, 41.3969036276823)
#
# # path = find_path(ox_g, g, src, dst)
# # plot_path(g, path, "path_map2.png")
# # plot(g, "city_map.png")
# show(g)
