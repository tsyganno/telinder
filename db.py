import sqlite3


class Sql_lite:

    def __init__(self):
        self.conn = sqlite3.connect('db/database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()

    def write_to_the_database(self, id: int, name_in_chat: str, id_user: int, first_name: str, last_name: str, username: str, date: str, age: int, gender: str, photo: str, photo_for_chat: str):
        """Добавление записи в БД, при условии, что flag_db == True"""
        self.cursor.execute(
            'INSERT INTO data (id, name_in_chat, id_user, first_name, last_name, username, date, age, gender, photo, photo_for_chat) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
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
                photo,
                photo_for_chat,
            )
        )
        self.conn.commit()

    def finding_a_duplicate_entry_in_the_database(self, user_id: int) -> bool:
        """Поиск повторяющейся записи в БД"""
        try:
            sql_select_query = """SELECT * FROM data WHERE id_user = ?"""
            self.cursor.execute(sql_select_query, (user_id,))
            records = self.cursor.fetchall()
            if len(records) > 0:
                return True
            else:
                return False
        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite (count)", error)

    def update_record_in_the_database(self, name_in_chat: str, id_user: int, first_name: str, last_name: str, username: str, date: str, age: int, gender: str, photo: str, photo_for_chat: str):
        """Обновление записи пользователя """
        try:
            group = (name_in_chat, first_name, last_name, username, date, age, gender, photo, photo_for_chat, id_user)
            sql_select_query = "UPDATE data SET name_in_chat = ?, first_name = ?, last_name = ?, username = ?, date = ?, age = ?, gender = ?, photo = ?, photo_for_chat = ? WHERE id_user = ?"
            self.cursor.execute(sql_select_query, group)
            self.conn.commit()

        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite (update)", error)

    def search_for_a_potential_partner(self, gender):
        """Поиск партнера противоположного пола"""
        try:
            sql_select_query = """SELECT * FROM data WHERE gender != ?"""
            self.cursor.execute(sql_select_query, (gender,))
            records = self.cursor.fetchall()
            return records
        except sqlite3.Error as error:
            print("Ошибка при работе с SQLite (partner)", error)
