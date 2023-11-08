import json

from be.model import error
from be.model import db_conn


class Seller(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def add_book(
            self,
            user_id: str,
            store_id: str,
            book_id: str,
            book_json_str: str,
            stock_level: int,
    ):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)
            self.conn.store_col.update_one(
                {"store_id": store_id},
                {
                    "$push": {
                        "books": {
                            "book_id": book_id,
                            "stock_level": stock_level
                        }
                    }
                }
            )
            self.conn.book_col.insert_one(json.loads(book_json_str))
        except BaseException as e:
            return 528, "{}".format(str(e))
        return 200, "ok"

    def add_stock_level(
            self, user_id: str, store_id: str, book_id: str, add_stock_level: int
    ):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)
            self.conn.store_col.update_one({"store_id": store_id, "books.book_id": book_id},  {"$inc": {"books.$.stock_level": add_stock_level}})
        except BaseException as e:
            return 528, "{}".format(str(e))
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)
            self.conn.store_col.insert_one({ 
                "store_id": store_id,
                "user_id": user_id,
                "books": []
            })
        except BaseException as e:
            return 528, "{}".format(str(e))
        return 200, "ok"