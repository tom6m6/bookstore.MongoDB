import logging
import pymongo
from pymongo import errors
from be.model import error
from be.model import db_conn


class Book(db_conn.DBConn):

    def __init__(self):
        db_conn.DBConn.__init__(self)

    def search_title_in_store(self, title: str, store_id: str, page_num: int, page_size: int):
        book = self.conn.book_col
        condition = {
            "title": title
        }
        result = book.find(condition,{"_id": 0}).skip((page_num - 1) * page_size).limit(page_size)
        result_list = list(result)
        if store_id != "":
            store = self.conn.store_col
            books_in_store = []
            for b in result_list:
                condition1 = {"store_id": store_id, "books.book_id": b.get('id')}
                book_id = list(store.find(condition1, {"books.book_id": 1}))
                if len(book_id) != 0:
                    books_in_store.append(b)
            result_list = books_in_store
        if len(result_list) == 0:
            return 501, f"{title} book not exist", []
        return 200, "ok", result_list

    def search_title(self, title: str, page_num: int, page_size: int):
        return self.search_title_in_store(title, "", page_num, page_size)

