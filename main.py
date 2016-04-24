import urllib2
import json
from pprint import pprint
import datetime
import sqlite3
from database import KingdomTable



class ApiHandler(object):
    """
    Connects to the OSRS web API to get GE JSON data

    Thanks goes out to the OP of this reddit post:
        https://www.reddit.com/r/2007scape/comments/3g06rq/guide_using_the_old_school_ge_page_api/

    attrs:
        idToJSON (dict(int: str)): A dictionary that maps the item ID of an OSRS item to its JSON data for the day
    """
    BASE_URL = 'http://services.runescape.com/m=itemdb_oldschool'
    URL = BASE_URL + '/api/catalogue/detail.json?item='


    def __init__(self):
        self.idToJSON = {}

    def reset(self):
        self.idToJSON = {}

    def query(self, id, retry = 0, force = False):
        if (not force and id in self.idToJSON.keys()):
            return self.idToJSON[id]
        if (retry > 15):
            raise Exception("TIMEOUT")
        query_target = self.URL + str(id)
        try:
            response = urllib2.urlopen(query_target)
            j = json.load(response)
        except ValueError:
            j = self.query(id, retry=retry + 1, force = force)
        self.idToJSON[id] = j
        return j

HANDLER = ApiHandler()

class GEItem(object):
    """
    The baseclass of a tradeable OSRS item

    attrs:
        json (str): The json string returned by the API handler
        id (int): The OSRS item id

    see also:
        https://www.reddit.com/r/2007scape/comments/3g06rq/guide_using_the_old_school_ge_page_api/
    """
    def __init__(self, id):
        self.json = HANDLER.query(id)
        self.id = id
        print str(self.id) + " => "


    def refresh(self, depth = 0):
        self.json = HANDLER.query(self.id)

    # The following are just simple accessor functions for the data
    def getIcon(self):
        return self.json['item']['icon']

    def getIconLarge(self):
        return self.json['item']['icon_large']

    def getId(self):
        return self.json['item']['id']

    def getCurrentTrend(self):
        return self.json['item']['current']['trend']

    def getCurrentPrice(self):
        return self.expand(self.json['item']['current']['price'])

    # Converts values such as 2.3m to 2300000 by checking the last letter and applying relevant
    # multiplication
    def expand(self, shorthand):
        if (type(shorthand) == int):
            return shorthand
        if shorthand.endswith('k'):
            return int(float(shorthand[:-1]) * 1000)
        elif shorthand.endswith('m'):
            return int(float(shorthand[:-1]) * 1000000)
        elif shorthand.endswith('b'):
            return int(float(shorthand[:-1]) * 1000000000)
        else:
            return int(shorthand.replace(",", ""))

class Index(object):
    """
    A class that combines an aggregate of GEItems and has a price that is a weighted average of all items in the Index

    attrs:
        IdToProb (dict(int: int)): A mapping of OSRS ids to their "probability" or their "weight"
            for example when you are getting a seed from a Birds nest, this class gets the expected value of
            the seeds you should pull. Another example is the expected value of getting an individual herb from
            your kingdom.

        items (list(GEItem)): A list of items that correspond with the item IDs from IdToProb
    """
    def __init__(self, idToProb):
        self.IdToProb = idToProb
        self.items = [GEItem(k) for k in self.IdToProb.keys()]

    def refresh(self):
        self.items = [GEItem(k) for k in self.IdToProb.keys()]

    def getCurrentPrice(self):
        """
        Returns the expected value of all items based on IdToProb
        """
        sum = 0.0
        for seed in self.items:
            sum += seed.getCurrentPrice() * self.IdToProb[seed.id]

        return int(sum)

class Herbs(Index):
    IdToProb = { # src: http://www.tip.it/runescape/pages/view/manage_thy_kingdom.htm
        203 : .22, #Tarromin
        205 : .198, #Harralander
        207 : .056, #Rannar
        209 :  .124, #Irit
        211 : .135, #Avantoe
        213 : .075, #Kwuarm
        215 : .064, #Cadantine
        217 : .062, #Dwarf Weed
        2485 : .067, #Lantadyme
    }
    def __init__(self):
        super(Herbs, self).__init__(self.IdToProb)

class BirdNest(GEItem):
    ID = 6693
    IdToProb = { # src: http://2007.runescape.wikia.com/wiki/Bird_nest
        5312 : .203, #Acorn
        5313 : .143, #Willow
        5314 : .059, #Maple
        5315 : .024, #Yew
        5316 : .011, #Magic
        5283 :  .146, #Apple
        5284 : .107, #Banana
        5285 : .08, #Orange
        5286 : .072, #Curry
        5287 : .054, #pineapple
        5288 : .043, #Papaya
        5289 : .032, #Palm
        5290 : .022 #Calquat

    }
    def __init__(self):
        super((BirdNest), self).__init__(self.ID)
        self.items = Index(self.IdToProb)

    def getCurrentPrice(self):
        return super(BirdNest, self).getCurrentPrice() + self.items.getCurrentPrice()

class KingdomItem(object):
    """
    Represents a resource you can set workers to in your Kingdom

    attrs:
        forcast(dict(int/Index : int): A mapping of OSRS item IDs or classes to how many are generated over a finite time
        days (int): how many days pass to generate the numbers represented by "forcast"
        name (str): The name of this object
    """
    def __init__(self, itemid_to_yield, name = None, days = 7):
        self.forcast = {} #assume 7 days
        self.days = days
        self.name = name
        for id, y in itemid_to_yield.iteritems():
            if (id == BirdNest.ID):
                self.forcast[BirdNest()] = y
                continue
            if (type(id) == int):
                self.forcast[GEItem(id)] = y
            else:
                self.forcast[id] = y

    def getYield(self):
        """
        :return: The expected gross value of the resources generated based on current prices
        """""
        sum = 0
        for key, value in self.forcast.iteritems():
            sum += key.getCurrentPrice() * value
        return sum

    def refresh(self):
        for key in self.forcast.keys():
            key.refresh()

class Kingdom(object):
    """
    The main class that represents the Kingdom of Miscellanea.

    attrs:
        data (dict(str: KingdomItem)): A mapping of column names in the SQL database in the Kingdom table to their
            respective KingdomItem objects

    see also:
        hard coded values are based on this: http://www.runehq.com/calculator/miscellania-management
    """
    def __init__(self):
        Trees = {1517 : 6051, BirdNest.ID : 60}
        Coal = {453 : 3706}
        Fish = {359 : 2988, 371 : 896}
        Cooked = {361 : 2988, 373 : 896}
        Flax = {1779 : 8487}
        Herb = {Herbs() : 410}
        Teak = {6333 : 2043, BirdNest.ID : 5}
        Mahog = {6332 : 1387, BirdNest.ID : 3}
        Both = {6333 : 826, 6332 : 826, BirdNest.ID : 4}
        self.data = {
            "Maples" : KingdomItem(Trees, "Trees"),
            "Coal" : KingdomItem(Coal, "Coal"),
            "Raw_Fish" : KingdomItem(Fish, "Raw Fish"),
            "Cooked_Fish" : KingdomItem(Cooked, "Cooked Fish"),
            "Flax" : KingdomItem(Flax, "Flax"),
            "Herbs" : KingdomItem(Herb, "Herbs"),
            "Teak" : KingdomItem(Teak, "Teak"),
            "Mahogany" : KingdomItem(Mahog, "Mahogany"),
            "Teak_and_Mahog" : KingdomItem(Both, "Teak + Mahog"),
        }

    def get_insertable(self):
        """
        a method to interface with the Database object

        returns a dictionary object with a mapping of column name to overall value
        """
        return {k : v.getYield() for k,v in self.data.iteritems()}

    def refresh(self):
        for item in self.data:
            item.refresh()
        self.data = sorted(self.data, key = KingdomItem.getYield, reverse=True)

    def __str__(self):
        return str( [item.name + ": " + str(item.getYield()) for item in self.data.values()] )

#used to test DB, since querying the API can be sluggish
TEST_DB = False
DB_TEST_CASE = {'Coal': 996914,
 'Cooked_Fish': 566076,
 'Flax': 84870,
 'Herbs': 666660,
 'Json': '{"5283": {"item": {"day180": {"trend": "neutral", "change": "0.0%"}, "name": "Apple tree seed", "day90": {"trend": "negative", "change": "-33.0%"}, "description": "Plant in a plantpot of soil to grow a sapling.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "neutral", "change": "0.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=5283", "current": {"trend": "neutral", "price": 4}, "members": "true", "type": "Default", "id": 5283, "today": {"trend": "neutral", "price": 0}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=5283"}}, "5284": {"item": {"day180": {"trend": "negative", "change": "-14.0%"}, "name": "Banana tree seed", "day90": {"trend": "negative", "change": "-40.0%"}, "description": "Plant in a plantpot of soil to grow a sapling.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "neutral", "change": "0.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=5284", "current": {"trend": "neutral", "price": 6}, "members": "true", "type": "Default", "id": 5284, "today": {"trend": "positive", "price": "+1"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=5284"}}, "6693": {"item": {"day180": {"trend": "negative", "change": "-27.0%"}, "name": "Crushed nest", "day90": {"trend": "negative", "change": "-21.0%"}, "description": "A crushed bird\'s nest.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-9.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=6693", "current": {"trend": "neutral", "price": "2,245"}, "members": "true", "type": "Default", "id": 6693, "today": {"trend": "positive", "price": "+76"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=6693"}}, "5286": {"item": {"day180": {"trend": "negative", "change": "-22.0%"}, "name": "Curry tree seed", "day90": {"trend": "negative", "change": "-14.0%"}, "description": "Plant in a plantpot of soil to grow a sapling.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-4.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=5286", "current": {"trend": "neutral", "price": 383}, "members": "true", "type": "Default", "id": 5286, "today": {"trend": "positive", "price": "+12"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=5286"}}, "5287": {"item": {"day180": {"trend": "negative", "change": "-46.0%"}, "name": "Pineapple seed", "day90": {"trend": "negative", "change": "-37.0%"}, "description": "Plant in a plantpot of soil to grow a sapling.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-21.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=5287", "current": {"trend": "neutral", "price": "2,845"}, "members": "true", "type": "Default", "id": 5287, "today": {"trend": "negative", "price": "- 67"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=5287"}}, "5288": {"item": {"day180": {"trend": "negative", "change": "-6.0%"}, "name": "Papaya tree seed", "day90": {"trend": "negative", "change": "-16.0%"}, "description": "Plant in a plantpot of soil to grow a sapling.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-10.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=5288", "current": {"trend": "neutral", "price": "8,477"}, "members": "true", "type": "Default", "id": 5288, "today": {"trend": "positive", "price": "+180"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=5288"}}, "5289": {"item": {"day180": {"trend": "positive", "change": "+0.0%"}, "name": "Palm tree seed", "day90": {"trend": "negative", "change": "-2.0%"}, "description": "Plant in a plantpot of soil to grow a sapling.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-6.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=5289", "current": {"trend": "neutral", "price": "40.2k"}, "members": "true", "type": "Default", "id": 5289, "today": {"trend": "negative", "price": "- 481"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=5289"}}, "5290": {"item": {"day180": {"trend": "negative", "change": "-47.0%"}, "name": "Calquat tree seed", "day90": {"trend": "negative", "change": "-20.0%"}, "description": "Plant in a plantpot of soil to grow a sapling.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-11.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=5290", "current": {"trend": "neutral", "price": 344}, "members": "true", "type": "Default", "id": 5290, "today": {"trend": "negative", "price": "- 1"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=5290"}}, "1779": {"item": {"day180": {"trend": "negative", "change": "-23.0%"}, "name": "Flax", "day90": {"trend": "negative", "change": "-33.0%"}, "description": "I should use this with a spinning wheel.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "neutral", "change": "0.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=1779", "current": {"trend": "neutral", "price": 10}, "members": "true", "type": "Default", "id": 1779, "today": {"trend": "neutral", "price": 0}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=1779"}}, "2485": {"item": {"day180": {"trend": "positive", "change": "+1.0%"}, "name": "Grimy lantadyme", "day90": {"trend": "negative", "change": "-7.0%"}, "description": "It needs cleaning.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-0.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=2485", "current": {"trend": "neutral", "price": "1,643"}, "members": "true", "type": "Default", "id": 2485, "today": {"trend": "negative", "price": "- 35"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=2485"}}, "6332": {"item": {"day180": {"trend": "positive", "change": "+28.0%"}, "name": "Mahogany logs", "day90": {"trend": "positive", "change": "+1.0%"}, "description": "Some well-cut mahogany logs.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-11.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=6332", "current": {"trend": "neutral", "price": 218}, "members": "true", "type": "Default", "id": 6332, "today": {"trend": "positive", "price": "+1"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=6332"}}, "6333": {"item": {"day180": {"trend": "positive", "change": "+52.0%"}, "name": "Teak logs", "day90": {"trend": "positive", "change": "+38.0%"}, "description": "Some well-cut teak logs.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "positive", "change": "+8.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=6333", "current": {"trend": "neutral", "price": 134}, "members": "true", "type": "Default", "id": 6333, "today": {"trend": "negative", "price": "- 1"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=6333"}}, "5312": {"item": {"day180": {"trend": "negative", "change": "-31.0%"}, "name": "Acorn", "day90": {"trend": "negative", "change": "-51.0%"}, "description": "Plant this in a plantpot of soil to grow a sapling.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-19.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=5312", "current": {"trend": "neutral", "price": 103}, "members": "true", "type": "Default", "id": 5312, "today": {"trend": "negative", "price": "- 1"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=5312"}}, "5313": {"item": {"day180": {"trend": "negative", "change": "-6.0%"}, "name": "Willow seed", "day90": {"trend": "negative", "change": "-17.0%"}, "description": "Plant this in a plantpot of soil to grow a sapling.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-9.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=5313", "current": {"trend": "neutral", "price": "8,980"}, "members": "true", "type": "Default", "id": 5313, "today": {"trend": "positive", "price": "+27"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=5313"}}, "5314": {"item": {"day180": {"trend": "negative", "change": "-3.0%"}, "name": "Maple seed", "day90": {"trend": "negative", "change": "-18.0%"}, "description": "Plant this in a plantpot of soil to grow a sapling.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-14.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=5314", "current": {"trend": "neutral", "price": "47.2k"}, "members": "true", "type": "Default", "id": 5314, "today": {"trend": "negative", "price": "- 760"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=5314"}}, "5315": {"item": {"day180": {"trend": "negative", "change": "-5.0%"}, "name": "Yew seed", "day90": {"trend": "negative", "change": "-22.0%"}, "description": "Plant this in a plantpot of soil to grow a sapling.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-1.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=5315", "current": {"trend": "neutral", "price": "88.8k"}, "members": "true", "type": "Default", "id": 5315, "today": {"trend": "negative", "price": "- 1,144"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=5315"}}, "5316": {"item": {"day180": {"trend": "positive", "change": "+1.0%"}, "name": "Magic seed", "day90": {"trend": "negative", "change": "-4.0%"}, "description": "Plant this in a plantpot of soil to grow a sapling.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-1.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=5316", "current": {"trend": "neutral", "price": "103.1k"}, "members": "true", "type": "Default", "id": 5316, "today": {"trend": "negative", "price": "- 1,057"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=5316"}}, "453": {"item": {"day180": {"trend": "positive", "change": "+40.0%"}, "name": "Coal", "day90": {"trend": "positive", "change": "+33.0%"}, "description": "Hmm a non-renewable energy source!", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "positive", "change": "+23.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=453", "current": {"trend": "neutral", "price": 269}, "members": "false", "type": "Default", "id": 453, "today": {"trend": "neutral", "price": 0}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=453"}}, "203": {"item": {"day180": {"trend": "positive", "change": "+26.0%"}, "name": "Grimy tarromin", "day90": {"trend": "negative", "change": "-6.0%"}, "description": "It needs cleaning.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-7.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=203", "current": {"trend": "neutral", "price": 71}, "members": "true", "type": "Default", "id": 203, "today": {"trend": "negative", "price": "- 2"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=203"}}, "205": {"item": {"day180": {"trend": "negative", "change": "-14.0%"}, "name": "Grimy harralander", "day90": {"trend": "negative", "change": "-29.0%"}, "description": "It needs cleaning.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-2.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=205", "current": {"trend": "neutral", "price": 509}, "members": "true", "type": "Default", "id": 205, "today": {"trend": "negative", "price": "- 3"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=205"}}, "207": {"item": {"day180": {"trend": "positive", "change": "+6.0%"}, "name": "Grimy ranarr weed", "day90": {"trend": "negative", "change": "-13.0%"}, "description": "It needs cleaning.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-5.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=207", "current": {"trend": "neutral", "price": "8,404"}, "members": "true", "type": "Default", "id": 207, "today": {"trend": "negative", "price": "- 23"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=207"}}, "209": {"item": {"day180": {"trend": "positive", "change": "+18.0%"}, "name": "Grimy irit leaf", "day90": {"trend": "negative", "change": "-7.0%"}, "description": "It needs cleaning.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-10.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=209", "current": {"trend": "neutral", "price": "1,270"}, "members": "true", "type": "Default", "id": 209, "today": {"trend": "negative", "price": "- 24"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=209"}}, "211": {"item": {"day180": {"trend": "negative", "change": "-7.0%"}, "name": "Grimy avantoe", "day90": {"trend": "negative", "change": "-6.0%"}, "description": "It needs cleaning.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-8.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=211", "current": {"trend": "neutral", "price": "2,406"}, "members": "true", "type": "Default", "id": 211, "today": {"trend": "negative", "price": "- 64"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=211"}}, "213": {"item": {"day180": {"trend": "negative", "change": "-27.0%"}, "name": "Grimy kwuarm", "day90": {"trend": "negative", "change": "-26.0%"}, "description": "It needs cleaning.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-14.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=213", "current": {"trend": "neutral", "price": "2,750"}, "members": "true", "type": "Default", "id": 213, "today": {"trend": "negative", "price": "- 21"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=213"}}, "215": {"item": {"day180": {"trend": "negative", "change": "-16.0%"}, "name": "Grimy cadantine", "day90": {"trend": "negative", "change": "-28.0%"}, "description": "It needs cleaning.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-17.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=215", "current": {"trend": "neutral", "price": "2,158"}, "members": "true", "type": "Default", "id": 215, "today": {"trend": "negative", "price": "- 32"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=215"}}, "217": {"item": {"day180": {"trend": "negative", "change": "-31.0%"}, "name": "Grimy dwarf weed", "day90": {"trend": "negative", "change": "-30.0%"}, "description": "It needs cleaning.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-9.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=217", "current": {"trend": "neutral", "price": "1,654"}, "members": "true", "type": "Default", "id": 217, "today": {"trend": "negative", "price": "- 42"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=217"}}, "5285": {"item": {"day180": {"trend": "negative", "change": "-31.0%"}, "name": "Orange tree seed", "day90": {"trend": "negative", "change": "-52.0%"}, "description": "Plant in a plantpot of soil to grow a sapling.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-38.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=5285", "current": {"trend": "neutral", "price": 11}, "members": "true", "type": "Default", "id": 5285, "today": {"trend": "negative", "price": "- 1"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=5285"}}, "359": {"item": {"day180": {"trend": "negative", "change": "-30.0%"}, "name": "Raw tuna", "day90": {"trend": "negative", "change": "-50.0%"}, "description": "I should try cooking this.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-15.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=359", "current": {"trend": "neutral", "price": 70}, "members": "false", "type": "Default", "id": 359, "today": {"trend": "negative", "price": "- 1"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=359"}}, "361": {"item": {"day180": {"trend": "negative", "change": "-34.0%"}, "name": "Tuna", "day90": {"trend": "negative", "change": "-48.0%"}, "description": "Wow, this is a big fish.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-17.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=361", "current": {"trend": "neutral", "price": 77}, "members": "false", "type": "Default", "id": 361, "today": {"trend": "negative", "price": "- 1"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=361"}}, "1517": {"item": {"day180": {"trend": "negative", "change": "-38.0%"}, "name": "Maple logs", "day90": {"trend": "negative", "change": "-37.0%"}, "description": "Logs cut from a maple tree.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-3.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=1517", "current": {"trend": "neutral", "price": 30}, "members": "false", "type": "Default", "id": 1517, "today": {"trend": "neutral", "price": 0}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=1517"}}, "371": {"item": {"day180": {"trend": "positive", "change": "+58.0%"}, "name": "Raw swordfish", "day90": {"trend": "positive", "change": "+23.0%"}, "description": "I should try cooking this.", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-7.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=371", "current": {"trend": "neutral", "price": 368}, "members": "false", "type": "Default", "id": 371, "today": {"trend": "negative", "price": "- 6"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=371"}}, "373": {"item": {"day180": {"trend": "positive", "change": "+51.0%"}, "name": "Swordfish", "day90": {"trend": "positive", "change": "+20.0%"}, "description": "I\'d better be careful eating this!", "typeIcon": "http://www.runescape.com/img/categories/Default", "day30": {"trend": "negative", "change": "-11.0%"}, "icon_large": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_big.gif?id=373", "current": {"trend": "neutral", "price": 375}, "members": "false", "type": "Default", "id": 373, "today": {"trend": "negative", "price": "- 3"}, "icon": "http://services.runescape.com/m=itemdb_oldschool/5167_obj_sprite.gif?id=373"}}}',
 'Mahogany': 336689,
 'Maples': 867990,
 'Raw_Fish': 538888,
 'Teak': 330967,
 'Teak_and_Mahog': 336516,
 'date': 'TEST_DATE'}


def main():
    db = KingdomTable()
    if not TEST_DB:
        #HANDLER.load()
        kingdom = Kingdom()

        insertable = kingdom.get_insertable()
        insertable["date"] = str(datetime.date.today())
        insertable["Json"] = json.dumps(HANDLER.idToJSON)
    else:
        insertable = DB_TEST_CASE
    pprint(insertable)
    #print kingdom
    #HANDLER.save()
    print datetime.date.today()
    db.insert_data(insertable)
    db.conn.close()

if __name__ == '__main__':
    main()

#HANDLER.save()

# END OF CLASS DECLARATION

# Build the URL

# Get the data from the URL

# Iterate over the json data
#for row in whip.json['item']:
#    print whip.json['item'][row]

# Create new GEItem instance
#print whip.getCurrentPrice()



# HERE IS THE RESPONSE FOR REFERENCE PURPOSES!
# {
#    "item":{
#       "icon":"http://services.runescape.com/m=itemdb_rs/4908_obj_sprite.gif?id=4151",
#       "icon_large":"http://services.runescape.com/m=itemdb_rs/4908_obj_big.gif?id=4151",
#       "id":4151,
#       "type":"Default",
#       "typeIcon":"http://www.runescape.com/img/categories/Default",
#       "name":"Abyssal whip",
#       "description":"A weapon from the abyss.",
#       "current":{
#          "trend":"neutral",
#          "price":"2.3m"
#       },
#       "today":{
#          "trend":"negative",
#          "price":"- 13.9k"
#       },
#       "members":"true",
#       "day30":{
#          "trend":"positive",
#          "change":"+4.0%"
#       },
#       "day90":{
#          "trend":"negative",
#          "change":"-10.0%"
#       },
#       "day180":{
#          "trend":"positive",
#          "change":"+41.0%"
#       }
#    }
# }