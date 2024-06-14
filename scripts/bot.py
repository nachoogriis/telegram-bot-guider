import os
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import random
from typing import Optional, TextIO
from typing import List, Tuple, Union
from typing_extensions import TypeAlias
import datetime
from city import *
import restaurants

Position: TypeAlias = Tuple[float, float]

####################################################################
# ---------------------- BOT INITIALIZATION ---------------------- #
####################################################################


TOKEN = open('token.txt').read().strip()
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

####################################################################
# --------------------------- COMMANDS --------------------------- #
####################################################################


def start(update, context):
    """ Builds the city graph, the list of restaurants and starts the
    conversation """

    # We initialize the user's data.
    context.user_data['restaurants']: restaurants.Restaurants = []
    context.user_data['location']: Tuple[Coord, Coord] = None
    context.user_data['accessibility']: bool = False

    # We get the user's username and salute the user.
    user_name = update.effective_chat.first_name
    message: str = ("Hola %s! Sóc EatingSubway, el bot que " +
                    "t'ajudarà a anar a qualsevol restaurant de """ +
                    "BCN.") % (user_name)

    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    message: str = ("Si encara no coneixes del tot el meu funcionament, " +
                    "sempre pots executar la comanda /help, que et " +
                    "mostrarà tot el que cal saber per utilitzar-me " +
                    "correctament.\n\nOn et vindria de gust anar?")

    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def help(update, context):
    """ Shows some basic information about the bot's functioning and detailed
    information about each command """
    message: str = ('''Bé, el primer que has de saber és que per tal ''' +
                    '''de que pugui funcionar correctament, cal que ''' +
                    '''comparteixis amb mi la teva *localització*. ''' +
                    '''Si encara no ho has fet, assegura't d'haver-ho ''' +
                    '''fet abans d'executar cap comanda que ho requereixi.'''
                    + '''\n\n A continuació, es mostren les diferents ''' +
                    '''comandes disponibles i el seu funcionament.\n\n''')

    # We print the instructions for each command
    for command in all_commands:
        message += ('''🔹 */''' + command + '''* ➡️ ''' +
                    all_commands[command] + '''\n''')

    context.bot.send_message(chat_id=update.effective_chat.id, text=message,
                             parse_mode=telegram.ParseMode.MARKDOWN)


def author(update, context):
    """ Shows the authors of the project """
    # We show the authors
    message: str = ('''Aquest projecte ha estat realitzat per:\n''' +
                    '''👩🏻‍💻 *Aïda Santacreu Perez*\n''' +
                    '''🧑🏻‍💻 *Ignacio Gris Martín*''')

    context.bot.send_message(chat_id=update.effective_chat.id, text=message,
                             parse_mode=telegram.ParseMode.MARKDOWN)


def find(update, context):
    """ Shows up to 12 restuarants that satisfy the given query """
    global all_rest
    try:
        # In case the number of parameters is wrong we notice the user
        assert(len(context.args) == 1), ("Wrong number of parameters")

        # We find the restaurants that satisfy the query
        query: str = context.args[0]
        list_rest: restaurants.Restaurants
        list_rest = restaurants.get_restaurants(query, all_rest)
        list_rest: restaurants.Restaurants = list_rest[:12]
        context.user_data['restaurants'] = list_rest

        # In case the list of restaurants is empty we notice the user
        assert(len(context.user_data['restaurants']) > 0), ("""No Restaurants
        Found""")

        # Otherwise we show the 12 first restaurants (sorted by ratio)
        message: str = '''S'han trobat els seguents restaurants:\n'''

        num_rest: int = 1
        for rest in list_rest:
            message += "\n" + str(num_rest) + " ➡️ " + str(rest.name) + "\n"
            num_rest += 1

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=message)

        # We show some help
        message: str = ('''Si després de veure els noms dels restaurants ''' +
                        '''encara no pots decidir-te, sempre pots executar '''
                        + '''la comanda */info <número>* per tal d'obtenir '''
                        '''més la comanda */info <número>* per tal ''' +
                        ''' d'obtenir més informació d'algun dels ''' +
                        '''restaurants. 😁''')

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=message,
                                 parse_mode=telegram.ParseMode.MARKDOWN)

    # Here are declared the possible errors of the function
    except AssertionError as msg:
        print(msg)
        if str(msg) == "No Restaurants Found":
            info: str = "No s'ha trobat cap restaurant que satisfaci la cerca."
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info)
        elif str(msg) == "Wrong number of parameters":
            info: str = ('''Nombre de paràmetres incorrecte. S'esperava ''' +
                         '''1 paràmetres i s'ha passat %d paràmetres. ''' +
                         '''Veure la comanda */help* per més ''' +
                         '''informació.''') % (len(context.args))
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info,
                                     parse_mode=telegram.ParseMode.MARKDOWN)


def info(update, context):
    """ Shows extra info from the asked restaurants """
    try:
        # If the number of parameters is wrong we notice the user
        assert(len(context.args) == 1), ("Wrong number of parameters")
        num: int = int(context.args[0]) - 1

        # If the index of the restaurant is wrong we notice the user
        assert(int(context.args[0]) > 0), ("Wrong Index")
        rest: restaurants.Restaurant = context.user_data['restaurants'][num]

        # Otherwise we show the restaurant's information
        message: str = ("""NAME ➡️ {}\nADDRESS ➡️ {}, {}\nDISTRICT ➡️ {}
PHONE ➡️ {}""".format(rest.name, rest.road_name, rest.start_street_num,
                      rest.district_name, rest.phone_num))

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=message)

    # Here are declared the errors of the function
    except AssertionError as msg:
        print(msg)
        if str(msg) == "Wrong number of parameters":
            info: str = ('''Nombre de paràmetres incorrecte. S'esperava ''' +
                         '''1 paràmetres i s'ha passat %d paràmetres. ''' +
                         '''Veure la comanda */help* per més ''' +
                         '''informació.''') % (len(context.args))
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info,
                                     parse_mode=telegram.ParseMode.MARKDOWN)

        elif str(msg) == "Wrong Index":
            info: str = ('''El valor del paràmetre passat no és ''' +
                         '''correcte. Hauria de ser major a 0''')
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info)

    except IndexError:
        print("Key Error")
        info: str = ("""El número introduït no es troba a la llista """ +
                     """de restaurants""")
        context.bot.send_message(chat_id=update.effective_chat.id, text=info)


def guide(update, context):
    """ Sends an image with the path from the user's location to the restaurant
    """
    global city_graph
    global access_city_graph
    global ox_g

    try:
        # In case the number of parameters is wrong we notice the user
        assert(len(context.args) == 1), ("Wrong number of parameters")

        # In case the parameter passed is not positive we notice the user
        assert(int(context.args[0]) > 0), ("Wrong Index")

        # In case the location has not been shared we notice the user
        assert(context.user_data['location'] is not None), "Location Error"
        num: int = int(context.args[0]) - 1
        rest: restaurants.Restaurant = context.user_data['restaurants'][num]

        src = context.user_data['location']
        dst: Tuple[Coord, Coord] = (rest.position[0], rest.position[1])

        # We use a certain graph using the accessibility information
        used_graph: CityGraph
        if context.user_data['accessibility']:
            used_graph = access_city_graph
        else:
            used_graph = city_graph

        # We find the path and create an image with the path plotted on it
        path = find_path(ox_g, used_graph, src, dst)
        user_name = update.effective_chat.first_name
        user_last_name = update.effective_chat.last_name
        rand_num: int = random.randint(1, 9999999)
        filename = (str(user_name) + str(user_last_name) + str(rand_num) +
                    ".png")
        plot_path(used_graph, path, filename)

        # We send the image to the user
        context.bot.send_photo(chat_id=update.effective_chat.id,
                               photo=open(filename, 'rb'))
        # We erase the image
        os.remove(filename)

    # Here are declared the errors of the function
    except AssertionError as msg:
        print(msg)

        if str(msg) == "Location Error":
            info = ("""Recorda que has de compartir la teva localització """ +
                    """abans de cridar la comanda /guide""")
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info)
        elif str(msg) == "Wrong number of parameters":
            info: str = ('''Nombre de paràmetres incorrecte. S'esperava ''' +
                         '''1 paràmetres i s'ha passat %d paràmetres. ''' +
                         '''Veure la comanda */help* per més ''' +
                         '''informació.''') % (len(context.args))
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info,
                                     parse_mode=telegram.ParseMode.MARKDOWN)
        elif str(msg) == "Wrong Index":
            info: str = ('''El valor del parámetre passat no és ''' +
                         '''correcte. Hauria de ser major a 0''')
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info)


    except IndexError:
        print("Key Error")
        info = "El número introduït no es troba a la llista de restaurants"
        context.bot.send_message(chat_id=update.effective_chat.id, text=info)


def time(update, context):
    """ Returns an aproximated total time taken to reach the given restaurant
    from the users location """

    global city_graph
    try:
        # In case the number of parameters is wrong we notice the user
        assert(len(context.args) == 1), ("Wrong number of parameters")

        # In case the parameter is not positive we notice the user
        assert(int(context.args[0]) > 0), ("Wrong Index")

        # In case the location has not been shared we notice the user
        assert(context.user_data['location'] is not None), "Location Error"

        # Otherwise we compute the total time taken to do the path
        num: int = int(context.args[0]) - 1
        rest: restaurants.Restaurant = context.user_data['restaurants'][num]
        src: Position = context.user_data['location']
        dst: Position = (rest.position[0], rest.position[1])
        ox_g: OsmnxGraph = get_osmnx_graph()

        path: Path = find_path(ox_g, city_graph, src, dst)
        time: float = travel_time(path, city_graph)

        info: str = """Trigaràs aproximadament {} minuts.""".format(time)
        context.bot.send_message(chat_id=update.effective_chat.id, text=info)

    # Here are declared the errors of the function
    except AssertionError as msg:
        print(msg)
        if str(msg) == "Location Error":
            info = ("""Recorda que has de compartir la teva localització """ +
                    """abans de cridar la comanda /guide""")
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info)
        elif str(msg) == "Wrong number of parameters":
            info: str = ('''Nombre de paràmetres incorrecte. S'esperava ''' +
                         '''1 paràmetres i s'ha passat %d paràmetres. ''' +
                         '''Veure la comanda */help* per més ''' +
                         '''informació.''') % (len(context.args))
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info,
                                     parse_mode=telegram.ParseMode.MARKDOWN)
        elif str(msg) == "Wrong Index":
            info: str = ('''El valor del parámetre passat no és ''' +
                         '''correcte. Hauria de ser major a 0''')
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info)

    except IndexError:
        print("Key Error")
        info: str = ("""El número introduït no es troba a la llista """ +
                     """de restaurants""")
        context.bot.send_message(chat_id=update.effective_chat.id, text=info)


def accessibility(update, context):
    """ Updates the accessibility variable, which is, by defauly, False """
    try:
        # In case the number of parameters is wrong we notice the user
        assert(len(context.args) == 1), ("Wrong number of parameters")
        access: str = context.args[0]

        # In case the parameter is wrong we notice the user
        assert(access == "yes" or access == "no"), ("Wrong parameter")

        # Otherwise we update the accessibility information
        if access == "yes":
            context.user_data['accessibility'] is False
            info: str = ("""Solicitud d'accessibilitat especial """ +
                         """acceptada. 👍🏼""")
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info)
        else:
            context.user_data['accessibility'] is True
            info: str = ("""Solicitud de retirar accessibilitat especial """ +
                         """acceptada. 👍🏼""")
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info)

    # Here are declared the errors of the function
    except AssertionError as msg:
        print(msg)
        if str(msg) == "Wrong number of parameters":
            info: str = ('''Nombre de paràmetres incorrecte. S'esperava ''' +
                         '''1 paràmetres i s'ha passat %d paràmetres. ''' +
                         '''Veure la comanda */help* per més ''' +
                         '''informació.''') % (len(context.args))
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info,
                                     parse_mode=telegram.ParseMode.MARKDOWN)
        elif str(msg) == "Wrong parameter":
            info: str = ("Paràmetre incorrecte. Veure la comanda " +
                         "*/help* per més informació.")
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=info,
                                     parse_mode=telegram.ParseMode.MARKDOWN)


def where(update, context):
    """ Saves the location of the user """
    message: str = '''Ubicació rebuda correctament!👍🏼'''
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    lon, lat = (update.message.location.latitude,
                update.message.location.longitude)
    context.user_data['location'] = (lat, lon)

####################################################################
# -------------- ALL COMMANDS AND IT'S HELP MESSAGES ------------- #
####################################################################


all_commands: dict = {
    'start': "Inicialitzaràs la conversa i es començarà a generar el graf " +
    "de la ciutat. 🏙",
    'help': "Et mostro totes les comandes disponibles, així com el seu " +
    "funcionament i el que requereixen. 📢",
    'author': "Mostra el nom de les dues persones que han realitzat el " +
    "projecte. 💻",
    'find <query>': "Troba fins a un màxim de 12 restaurants " +
    "que satisfacin la cerca donada i en mostra els seus noms per tal de " +
    "que l'usuari pugui escollir a quin anar. Es complementa amb la comanda" +
    " */info <número>*. 🍽",
    'info <number>': "Mostra informació adicional d'algun dels restaurants " +
    "proporcionats per la funció */find <numero>*. 📝",
    'guide <number>': "Calcula el camí més curt fins al restaurant indicat " +
    "ja sigui a peu, en metro, o combinant-ho. A més, envia una foto a " +
    "l'usuari amb la ruta que s'ha de seguir per arribar al destí. 🗺",
    'time <number>': "Calcula el temps aproximat que es trigaria en anar" +
    "desde la posició de l'usuari fins al restaurant indicat. ⏱",
    'acessibility <yes/no>': "Serveix per a que l'usuari especifiqui si" +
    "es necessita access especial als accessos. D'aquesta forma no es tenen" +
    "en compte aquells camins que incloguin accessos no accessibles"
}

####################################################################
# --------------------------- HANDLERS --------------------------- #
####################################################################


dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('author', author))
dispatcher.add_handler(CommandHandler('find', find))
dispatcher.add_handler(CommandHandler('info', info))
dispatcher.add_handler(CommandHandler('guide', guide))
dispatcher.add_handler(CommandHandler('time', time))
dispatcher.add_handler(CommandHandler('accessibility', accessibility))
dispatcher.add_handler(MessageHandler(Filters.location, where))

####################################################################
# ----------------------- GLOABL VARIABLES ----------------------- #
####################################################################


print("-------------------------------------")
print("Loading all restaurants...")
all_rest: restaurants.Restaurants = restaurants.read()
print("Loading street graph...")
ox_g: OsmnxGraph = get_osmnx_graph()
print("Loading city graph...")
city_graph: CityGraph = get_city_graph(False)
# Graph with special accessibility
print("Loading city accessibility graph...")
access_city_graph: CityGraph = get_city_graph(True)
print("Bot initialized")
print("-------------------------------------")

#####################################################################
# ------------------------ BOT INITIALIZER ------------------------ #
#####################################################################


updater.start_polling()
