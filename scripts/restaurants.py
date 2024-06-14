from dataclasses import dataclass
import pandas as pd  # type: ignore
from typing import List, Tuple
from typing_extensions import TypeAlias
from fuzzysearch import find_near_matches  # type: ignore
from fuzzywuzzy import fuzz  # type: ignore
import operator  # type: ignore

Coord: TypeAlias = Tuple[float, float]


@dataclass
class Restaurant:

    # RESTAURANT CLASS ATTRIBUTES

    name: str
    road_name: str
    start_street_num: str
    neighborhood_name: str
    district_name: str
    phone_num: str
    position: Coord


Restaurants = List[Restaurant]


def read() -> Restaurants:
    """ Llegeix el fitxer de restaurants i en retorna una llista amb tots els
    restaurants del fitxer """

    # Columns used from the ones in the url file
    used_columns: List = ["name", "addresses_road_name",
                          "addresses_start_street_number",
                          "addresses_neighborhood_name",
                          "addresses_district_name", "values_value",
                          "geo_epgs_4326_x", "geo_epgs_4326_y"]

    # Specified data types for each column / attribute
    column_types: dict = {
        "name": str,
        "addresses_road_name": str,
        "addresses_start_street_number": str,
        "addresses_neighborhood_name": str,
        "addresses_district_name": str,
        "values_value": str,
        "geo_epgs_4326_x": float,
        "geo_epgs_4326_y": float
    }

    # We read the csv file and save it's data as a pandas data frame
    df = pd.read_csv("restaurants.csv", usecols=used_columns,
                     dtype=column_types, keep_default_na=False)

    restaurants_list: Restaurants = []

    # We iterate through each "restaurant" to save it's data as an object
    # (Restaurant object)
    prev_name: str = ""
    for row in df.itertuples():
        # We create the access and add it to the accesses list
        if row.name != prev_name:
            rest_pos: Coord = (row.geo_epgs_4326_y, row.geo_epgs_4326_x)
            r: Restaurant = Restaurant(row.name, row.addresses_road_name,
                                       row.addresses_start_street_number,
                                       row.addresses_neighborhood_name,
                                       row.addresses_district_name,
                                       row.values_value, rest_pos)
            restaurants_list.append(r)
        prev_name = row.name

    return restaurants_list


def find_logic(query: List, restaurants: Restaurants) -> Restaurants:
    """ Given a query (as a list), returns a sorted list (by ratio) with all
    the restaurants that satisfy the given query """

    # We create two dictionaries. One to save the restaurants that match the
    # query and its ratio, the other to register the attributes of every
    # restaurant.
    info_rest: dict = {}
    satisfy_ratio: dict = {}
    sorted_satisfy: Restaurants = []

    # We iterate through every restaurant of the list, checking whether they
    # chek the query.
    for rest in restaurants:
        ratio: List = [0]
        bool_ratio: bool = evaluate(query, [0], rest, ratio)
        # If the restaurant matches, we add the restaurant with it's ratio  and
        # attributes to the dictionaries.
        if bool_ratio:
            info_rest[rest.name] = rest
            satisfy_ratio[rest.name] = ratio[0]

    # Function to sort the dictionary of restaurants that satisfy the query by
    # it's ratio (form higher to lower)
    sorted_by_ratio = sorted(satisfy_ratio.items(),
                             key=operator.itemgetter(1), reverse=True)

    # Using the dictionary with the attributes, we add the restaurants  that
    # match (previously sorted) and it's information to the list of matches
    # that we will return.
    for sort_rest in sorted_by_ratio:
        # print(sort_rest[1])
        restaurant = info_rest[sort_rest[0]]
        # print("{}\n".format(restaurant))
        sorted_satisfy.append(restaurant)

    return sorted_satisfy


def evaluate(query: List, cont: List, restaurant: Restaurant,
             ratio: List) -> bool:
    """ Evalua de manera recursiva si el restaurant donat compleix amb la
    expresió lógica donada. Retorna un boleà (True si compleix, False si no
    compleix) """

    s: str = query[cont[0]]
    cont[0] = cont[0]+1

    if s == "and":
        attr1 = evaluate(query, cont, restaurant, ratio)
        attr2 = evaluate(query, cont, restaurant, ratio)
        return attr1 and attr2

    elif s == "or":
        attr1 = evaluate(query, cont, restaurant, ratio)
        attr2 = evaluate(query, cont, restaurant, ratio)
        return attr1 or attr2

    elif s == "not":
        attr1 = evaluate(query, cont, restaurant, ratio)
        return not attr1

    else:
        evaluate_rest: bool = find(s, restaurant, ratio)
        return evaluate_rest


def find(query: str, rest: Restaurant, ratio: List) -> bool:
    """Evalua si el restaurant donat compleix el requisit donat i retorna un
    boleà. Actualitza el ratio si el restaurant satisfà la cerca"""

    cols: List = [rest.name, rest.road_name, rest.neighborhood_name,
                  rest.district_name]

    # We iterate through every attribute of the restaurant checking if any
    # matches with the query requested
    bool_1: bool = False
    for attr in cols:
        if (type(attr) == str and find_near_matches(query.lower(),
            attr.lower(), max_l_dist=int(len(query)*0.25), max_deletions=0,
           max_insertions=int(len(query)*0.25))):

            # If the attribute matches the query we update the matching ratio
            # of the attribute with the query
            matched: str = str(find_near_matches(query.lower(),
                               attr.lower(), max_l_dist=int(len(query)*0.25),
                               max_deletions=0,
                               max_insertions=int(len(query)*0.25)))
            matching_word: str = matched.split(" ")[3][9:-2]

            ratio[0] += fuzz.ratio(query.lower(), matching_word)
            bool_1 = True

    return bool_1


def good_format(query: str) -> str:
    """ Given a query, it returns the same query but in a good format in order
    to split it into a list """
    chars: str = "(),"
    for i in chars:
        query = query.replace(i, " ")
    return query


def get_restaurants(query: str, restaurants: Restaurants) -> Restaurants:
    """ Gets a ist of the restuarants that satisfy the
    given query"""
    r: Restaurants = read()
    # We split the query into a list so that we can execute the logical serve
    q_list: List = good_format(query).split()
    list_rest = find_logic(q_list, r)
    return list_rest


def main() -> None:
    r = read()
    query = "and(pizza,eixample)"
    satisfy = get_restaurants(query, r)
    # string = str(find_near_matches("pizz", "pizza", max_l_dist=1)[0])
    # final = string.split(" ")[3][9:-2]
    # print(final)
    print("\n")
    # for rest in satisfy:
    #     print("{}\n".format(rest))
    # print(len(satisfy))
    for rest in satisfy[:12]:
        print("{}\n".format(rest))


# main()
