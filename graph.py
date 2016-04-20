import matplotlib
import numpy as np
from matplotlib import pyplot #Download this dependency via PIP!
from database import KingdomDB

GRAPH_OPTIONS = [c + "o-" for c in "bgrcmyk"] + [c + "^--" for c in "bgrcmyk"]

def draw_data():
    COST = 350000

    db = KingdomDB()
    dict = db.query_plottable()

    fig, ax = pyplot.subplots()
    fig.canvas.draw()

    #labels = ["" for item in ax.get_xticklabels()]
    #labels[0] = dict["date"][0]
    #labels[-1] = dict["date"][-1]

    #ax.set_xticklabels(labels)



    pyplot.grid()
    lines = []
    names = []
    for i, (k, v) in enumerate(dict.iteritems()):
        if (k == "date"):
            continue
        p = pyplot.plot([elem - COST for elem in v], GRAPH_OPTIONS[i-1], label = str(k))
        lines.append(p)
    print names
    leg = pyplot.legend(loc = "lower left")
    pyplot.draw()
    pyplot.xticks(np.arange(len(dict["date"])), dict["date"])
    print [item.get_label() for item in ax.get_yticklabels()]
    pyplot.show()

    db.conn.close()



if __name__ == '__main__':
    draw_data()