import sqlite3, os
KINGDOM_TABLE_NAME = "Kingdom"
FARM_TABLE_NAME = "Farm"
DB_PATH = "C:\Users\Kyle\PycharmProjects\Kingdom-Rewards-Calculator"

CREATE_TABLES_QUERY = """
    CREATE TABLE IF NOT EXISTS """ + KINGDOM_TABLE_NAME + """ (
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

    CREATE TABLE IF NOT EXISTS """ + FARM_TABLE_NAME + """ (
        id Integer PRIMARY KEY AUTOINCREMENT,
        date text UNIQUE,
        Json text
    )

"""

KINGDOM_TABLE_COL_LIST = ["date", "Coal", "Herbs", "Maples", "Cooked_Fish", "Raw_Fish", "Teak", "Teak_and_Mahog", "Mahogany", "Flax", "Json"]

INSERT_INTO_KINGDOM_TABLE_QUERY = """
    INSERT INTO """ + KINGDOM_TABLE_NAME + """ ({}) VALUES (?,?,?,?,?,?,?,?,?,?,?)
"""

MAIN_KINGDOM_QUERY = """
    SELECT *
    FROM
        (SELECT """ + ",".join(KINGDOM_TABLE_COL_LIST[:-1]) + """ FROM Kingdom ORDER BY date desc {})
    ORDER BY date asc
"""

class Database(object):
    """
    The baseclass for interacting with the SQLite Database
    """
    FileName = "\kingdom.db"
    def __init__(self):
        assert os.path.exists(DB_PATH + self.FileName)
        self.conn = sqlite3.connect(DB_PATH + self.FileName)

    def __del__(self):
        self.conn.close()

    def get_cursor(self):
        return self.conn.cursor()

    def generate_insert_query(self, dict, table_name):
        cols = dict.keys()
        vals = "?" * len(dict.values())
        return """
            INSERT INTO """ + table_name + """ ({}) VALUES ({})
        """.format(",".join(cols), ",".join(vals))

    def insert_data(self, dict, table_name):
        c = self.get_cursor()
        q = self.generate_insert_query(dict, table_name)
        print q
        c.execute(q, dict.values())
        self.conn.commit()

class KingdomTable(Database):
    TableName = KINGDOM_TABLE_NAME
    def insert_data(self, dict):
        super(KingdomTable, self).insert_data(dict, self.TableName)

    def query_plottable(self, limit = None):
        if (limit is None):
            limit = ""
        elif (type(limit) == int):
            limit = "LIMIT " + str(limit)
        else:
            raise Exception("limit is wrong type. Must be int or Nonetype")

        q = MAIN_KINGDOM_QUERY.format(limit)
        c = self.get_cursor()
        print q
        c.execute(q)
        rows = c.fetchall()
        data = {k : [] for k in KINGDOM_TABLE_COL_LIST[:-1]}
        for row in rows:
            for i, col in enumerate(row):
                data[KINGDOM_TABLE_COL_LIST[i]].append(col)
        return data



if __name__ == '__main__':
    conn = sqlite3.connect("kingdom.db")
    c = conn.cursor()
    c.execute(CREATE_TABLES_QUERY)

    #c.execute("""
    #INSERT INTO Kingdom
    #(date, Coal, Maples, Herbs, Cooked_Fish, Raw_Fish, Teak, Teak_and_Mahog, Mahogany, Flax)
    #VALUES ('2016-04-16',974678,916263,704790,597140,562488,376380,354218,335421,84870)""")
    #c.execute("""
    #INSERT INTO Kingdom
    #(date, Coal, Maples, Herbs, Cooked_Fish, Raw_Fish, Teak, Teak_and_Mahog, Mahogany, Flax)
    #VALUES ('2016-04-17',1015444,906603,692900,601620,557708,375575,353574,334938,84870)""")

    conn.commit()
    conn.close()