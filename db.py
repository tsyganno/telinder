import sqlite3


class Sql_lite:

    def __init__(self):
        self.conn = sqlite3.connect('db/database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()

    def write_to_the_database(self, id: int, name_in_chat: str, id_user: int, first_name: str, last_name: str, username: str, date: str, age: int, gender: str, photo: str):
        """Добавление записи в БД, при условии, что flag_db == True"""
        self.cursor.execute(
            'INSERT INTO data (id, name_in_chat, id_user, first_name, last_name, username, date, age, gender, photo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (
                id,
                name_in_chat,
                id_user,
                first_name,
                last_name,
                username,
                date,
                age,
                gender,
                photo
            )
        )
        self.conn.commit()

    def finding_a_duplicate_entry_in_the_database(self, text: str) -> bool:
        """Поиск повторяющейся записи в БД"""
        try:
            sql_select_query = """SELECT * FROM data WHERE text = ?"""
            self.cursor.execute(sql_select_query, (text,))
            records = self.cursor.fetchall()
            if len(records) > 0:
                return True
            else:
                return False
        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite", error)

    def deleting_extra_entries(self):
        """Удаление лишних записей, начинается после 1000 шт"""
        try:
            while True:
                sql_select_query = """SELECT * FROM data"""
                self.cursor.execute(sql_select_query)
                records = self.cursor.fetchall()
                if len(records) > 1000:
                    sql_select_query = """DELETE FROM data WHERE id = (SELECT min(id) FROM data)"""
                    self.cursor.execute(sql_select_query)
                    self.conn.commit()
                else:
                    break
        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite", error)
