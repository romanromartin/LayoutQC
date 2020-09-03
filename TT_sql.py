import mysql.connector


class TT_sql:

    def __init__(self):

        try:
            self.cnx = mysql.connector.connect(user='root', password='74107410', host='localhost', database='tech_treb')
            self.cursor = self.cnx.cursor()
        except mysql.connector.Error as err:
            print("Something went wrong: {}".format(err))

        self.translate_tables = (
            'air_borispol', 'Аэропорт Борисполь', 'air_dnepr', 'Аэропорт Днепр', 'air_kharkov', 'Аэропорт Харьков',
            'air_lvov', 'Аэропорт Львов',
            'air_odessa', 'Аэропорт Одесса', 'air_zaporoje', 'Аэропорт Запорожье', 'intercity', 'Интерсити',
            'metro_kharkov', 'Метро Харьков', 'metro_kiev', 'Метро Киев',
            'naruj_kharkov', 'Наружка Харьков', 'transport', 'Транспорт')
        self.tables = self.show_tables()
        self.result = []
        self.result_one_percent = []

    def show_tables(self):
        queryTT = "SHOW TABLES"
        self.cursor.execute(queryTT)
        results = []
        b = ''
        for TABLES in self.cursor:
            a = str(TABLES)[2:-3]
            i = 0
            while i < len(self.translate_tables):
                if a == self.translate_tables[i]:
                    b = self.translate_tables[i + 1]
                i += 1
            results.append(b)
        return results

    def table_Activated(self, name_table_activate):
        self.locations = []
        i = 0
        while i < len(self.translate_tables):
            if name_table_activate == self.translate_tables[i]:
                self.name_table_activate = self.translate_tables[i - 1]
            i += 1
        query_location = ("SELECT location FROM " + self.name_table_activate)
        self.cursor.execute(query_location)
        for c in self.cursor:
            d = str(c)[2:-3]
            if d in self.locations:
                continue
            else:
                self.locations.append(d)
        return self.locations

    def location_Activated(self, name_location_activate):
        self.name_tt = []
        self.name_location_activate = name_location_activate
        query_name_tt = (
                'SELECT name_tt FROM ' + self.name_table_activate + ' WHERE location = ' + "'" + self.name_location_activate + "'")
        self.cursor.execute(query_name_tt)
        for e in self.cursor:
            d = (str(e)[2:-3])
            if d in self.name_tt:
                continue
            else:
                self.name_tt.append(d)
        return self.name_tt

    def name_Activated(self, name_name_activate):
        self.name_name_activate = name_name_activate
        self.code_tt = []
        query_code_tt = (
                'SELECT code_tt FROM ' + self.name_table_activate + ' WHERE location = ' + "'"
                + self.name_location_activate + "'" + 'AND name_tt = ' + "'" + self.name_name_activate + "'")
        self.cursor.execute(query_code_tt)
        for f in self.cursor:
            r = str(f)[2:-3]
            self.code_tt.append(r)
        if len(self.code_tt) > 1:
            self.code_tt += ['выбрать несколько конструкций']
        return self.code_tt

    def tt_value(self):
        query_tt_value = ('SELECT dpi, dis_x, dis_y FROM ' + self.name_table_activate + ' WHERE location = ' + "'"
                          + self.name_location_activate + "'" + ' AND name_tt = ' + "'" + self.name_name_activate + "'")
        self.cursor.execute(query_tt_value)
        param_tt = ''
        for (dpi, dis_x, dis_y) in self.cursor:
            param_tt = str('↔ {},mm ↨ {},mm \n Разрешение: {}dpi'.format(dis_x, dis_y, dpi)).replace(',', '')
        return param_tt

    def Auto_SelectTT(self, width_layout, height_layout):
        self.result = []
        self.result_one_percent = []
        queryTT = "SHOW TABLES"
        self.cursor.execute(queryTT)
        self.tablesTT = []
        rus_tables = ''

        for TABLES in self.cursor:
            a = str(TABLES)[2:-3]
            self.tablesTT.append(a)
        for k in self.tablesTT:
            # print(k)
            i = 0
            while i < len(self.translate_tables):
                if k == self.translate_tables[i]:
                    rus_tables = self.translate_tables[i + 1]
                i += 1
            queryAutoTT = ('SELECT  location, name_tt, code_tt FROM ' + k + ' WHERE dis_x = ' + str(
                width_layout) + ' AND dis_y = ' + str(height_layout))

            self.cursor.execute(queryAutoTT)
            for l in self.cursor:
                m = []
                m.append(rus_tables)
                for item in l:
                    m.append(item)
                self.result.append(m)

            if width_layout < 1000:
                coeficient = 10
            else:
                coeficient = 40

            queryAutoTT_one_percent = ('SELECT  location, name_tt, code_tt FROM ' + k
                                       + ' WHERE dis_x > ' + str(width_layout - coeficient)
                                       + ' AND dis_x < ' + str(width_layout + coeficient)
                                       + ' AND dis_y > ' + str(height_layout - coeficient)
                                       + ' AND dis_y < ' + str(height_layout + coeficient))
            self.cursor.execute(queryAutoTT_one_percent)
            for d in self.cursor:
                line_result_one_percent = []
                line_result_one_percent.append(rus_tables)
                for item in d:
                    line_result_one_percent.append(item)
                self.result_one_percent.append(line_result_one_percent)
            for n in self.result:
                if n in self.result_one_percent:
                    self.result_one_percent.remove(n)

    def CheckLayOut_func_sql(self):
        self.cursor.execute("SHOW TABLES")
        tablesTT = []
        for TABLES in self.cursor:
            a = str(TABLES)[2:-3]
            tablesTT.append(a)
        for k in tablesTT:
            query_all_TT_value = (
                    'SELECT * FROM ' + k
                    + ' WHERE name_tt = ' + "'" + self.name_name_activate + "'")
            self.cursor.execute(query_all_TT_value)
            for l in self.cursor:
                m = []
                for item in l:
                    m.append(item)
        return m
