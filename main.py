import urllib2
import json



class GEItem(object):
    BASE_URL = 'http://services.runescape.com/m=itemdb_oldschool'
    URL = BASE_URL + '/api/catalogue/detail.json?item='
    MEMO = {}

    # Constructor for GEItem  - only takes in the JSON data we got from CURL
    def __init__(self, id):
        self.json = None
        self.id = id
        self.query_target = self.URL + str(id)
        print str(self.id) + " => " + str(self.refresh())


    def refresh(self, depth = 0):
        if depth > 15:
            print "TIMEOUT"
            return
        try:
            response = urllib2.urlopen(self.query_target)
            j = json.load(response)
        except ValueError:
            j = self.refresh(depth=depth + 1)
        self.json = j
        return self.json

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
    def __init__(self, idToProb):
        self.IdToProb = idToProb
        self.items = [GEItem(k) for k in self.IdToProb.keys()]

    def refresh(self):
        self.items = [GEItem(k) for k in self.IdToProb.keys()]

    def getCurrentPrice(self):
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
        self.items = [GEItem(k) for k in self.IdToProb.keys()]

    def refresh(self):
        ret = super((BirdNest), self).refresh()
        self.items = [GEItem(k) for k in self.IdToProb.keys()]
        return ret

    def _getExpectedValue(self):
        sum = 0.0
        for seed in self.items:
            sum += seed.getCurrentPrice() * self.IdToProb[seed.id]

        return int(sum)

    def getCurrentPrice(self):
        return super(BirdNest, self).getCurrentPrice() + self._getExpectedValue()

nest = BirdNest()

class KingdomItem(object):
    def __init__(self, itemid_to_yield, name, days = 7):
        self.forcast = {} #assume 7 days
        self.days = days
        self.name = name
        for id, y in itemid_to_yield.iteritems():
            if (id == BirdNest.ID):
                self.forcast[nest] = y
                continue
            if (type(id) == int):
                self.forcast[GEItem(id)] = y
            else:
                self.forcast[id] = y

    def getYield(self):
        sum = 0
        for key, value in self.forcast.iteritems():
            sum += key.getCurrentPrice() * value
        return sum

    def refresh(self):
        for key in self.forcast.keys():
            key.refresh()

class Kingdom(object):#src http://www.runehq.com/calculator/miscellania-management
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
        self.list = [KingdomItem(Trees, "Trees"),
                     KingdomItem(Coal, "Coal"),
                     KingdomItem(Fish, "Raw Fish"),
                     KingdomItem(Cooked, "Cooked Fish"),
                     KingdomItem(Flax, "Flax"),
                     KingdomItem(Herb, "Herbs"),
                     KingdomItem(Teak, "Teak"),
                     KingdomItem(Mahog, "Mahogany"),
                     KingdomItem(Both, "Teak + Mahog"),
                     ]
        self.list = sorted(self.list, key = KingdomItem.getYield, reverse=True)

    def refresh(self):
        for item in self.list:
            item.refresh()
        self.list = sorted(self.list, key = KingdomItem.getYield, reverse=True)

    def __str__(self):
        return str( [item.name + ": " + str(item.getYield()) for item in self.list] )

kingdom = Kingdom()
print kingdom


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