import matplotlib
from matplotlib import pyplot #Download this dependency via PIP!
from database import KingdomDB

def draw_data():
    GRAPH_OPTIONS = [c + "o-" for c in "bgrcmyk"] + [c + "^--" for c in "bgrcmyk"]

    COST = 350000

    db = KingdomDB()
    dict = db.query_plottable()

    for i, (k, v) in enumerate(dict.iteritems()):
        if (k == "date"):
            continue
        p = pyplot.plot([elem - COST for elem in v], GRAPH_OPTIONS[i-1])

    db.conn.close()
    pyplot.show()


if __name__ == '__main__':
    draw_data()