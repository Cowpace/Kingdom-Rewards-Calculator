import sqlite3
DB_NAME = "Kingdom"

CREATE_TABLES_QUERY = """
    CREATE TABLE IF NOT EXISTS """ + DB_NAME + """ (
        id Integer PRIMARY KEY AUTOINCREMENT,
        date text UNIQUE,
        Coal Integer,
        Herbs Integer,
        Maples Integer,
        Cooked_Fish Integer,
        Raw_Fish Integer,
        Teak Integer,
        Teak_and_Mahog Integer,
        Mahogany Integer,
        Flax Integer,
        Json text
    )

"""

KINGDOM_TABLE_COL_LIST = ["date", "Coal", "Herbs", "Maples", "Cooked_Fish", "Raw_Fish", "Teak", "Teak_and_Mahog", "Mahogany", "Flax", "Json"]

INSERT_INTO_KINGDOM_TABLE_QUERY = """
    INSERT INTO """ + DB_NAME + """ ({}) VALUES (?,?,?,?,?,?,?,?,?,?,?)
"""

class KingdomDB(object):
    def __init__(self):
        self.conn = sqlite3.connect("kingdom.db")

    def __del__(self):
        self.conn.close()

    def insert_data(self, dict):
        li = dict.values()
        c = self.conn.cursor()
        print INSERT_INTO_KINGDOM_TABLE_QUERY.format(",".join(dict.keys()))
        c.execute(INSERT_INTO_KINGDOM_TABLE_QUERY.format(",".join(dict.keys())), tuple(li))
        self.conn.commit()


if __name__ == '__main__':
    conn = sqlite3.connect("kingdom.db")
    c = conn.cursor()
    c.execute("drop table if exists Kingdom")
    c.execute(CREATE_TABLES_QUERY)
    c.execute("""
    INSERT INTO Kingdom
    (date, Coal, Maples, Herbs, Cooked_Fish, Raw_Fish, Teak, Teak_and_Mahog, Mahogany, Flax)
    VALUES ('2016-04-16',974678,916263,704790,597140,562488,376380,354218,335421,84870)""")
    c.execute("""
    INSERT INTO Kingdom
    (date, Coal, Maples, Herbs, Cooked_Fish, Raw_Fish, Teak, Teak_and_Mahog, Mahogany, Flax)
    VALUES ('2016-04-17',1015444,906603,692900,601620,557708,375575,353574,334938,84870)""")

    conn.commit()
    conn.close()