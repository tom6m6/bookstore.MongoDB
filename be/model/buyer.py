import uuid
import json
import logging
from be.model import db_conn
from be.model import error
from datetime import datetime, timedelta


class Buyer(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))
            total_price = 0
            for book_id, count in id_and_count:
                result = self.conn.store_col.find_one({"store_id": store_id, "books.book_id": book_id}, {"books.$": 1})
                if not result:
                    return error.error_non_exist_book_id(book_id) + (order_id,)
                result1 = self.conn.book_col.find_one({"id": book_id})
                stock_level = result["books"][0]["stock_level"]
                #book_info = json.loads(result["books"][0]["book_info"])
                #price = book_info["price"]
                price = result1["price"]
                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)

                result = self.conn.store_col.update_one({"store_id": store_id, "books.book_id": book_id, "books.stock_level": {"$gte": count}},
                                                               {"$inc": {"books.$.stock_level": -count}})

                if result.modified_count == 0:
                    return error.error_stock_level_low(book_id) + (order_id,)

                self.conn.order_detail_col.insert_one({
                    "order_id": uid,
                    "book_id": book_id,
                    "count": count,
                    "price": price
                })

                total_price += price * count
            now_time = datetime.utcnow()
            self.conn.order_col.insert_one({
                "order_id": uid,
                "store_id": store_id,
                "user_id": user_id,
                "create_time": now_time,
                "price": total_price,
                "status": 0
            })
            order_id = uid

        except BaseException as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            result = self.conn.order_col.find_one({"order_id": order_id, "status": 0})
            if result is None:
                return error.error_invalid_order_id(order_id)
            buyer_id = result["user_id"]
            store_id = result["store_id"]
            total_price = result["price"]
            if buyer_id != user_id:
                return error.error_authorization_fail()


            result = self.conn.user_col.find_one({"user_id": buyer_id})
            if result is None:
                return error.error_non_exist_user_id(buyer_id)
            balance = result.get("balance", 0)
            if password != result.get("password", ""):
                return error.error_authorization_fail()


            result = self.conn.store_col.find_one({"store_id": store_id})
            # result = self.conn.user_store_col.find_one({"store_id": store_id})
            if result is None:
                return error.error_non_exist_store_id(store_id)
            seller_id = result.get("user_id")
            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)


            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)
            result = self.conn.user_col.update_one({"user_id": buyer_id, "balance": {"$gte": total_price}}, {"$inc": {"balance": -total_price}})
            if result.matched_count == 0:
                return error.error_not_sufficient_funds(order_id)


            result = self.conn.user_col.update_one({"user_id": seller_id}, {"$inc": {"balance": total_price}})
            if result.matched_count == 0:
                return error.error_non_exist_user_id(buyer_id)


            self.conn.order_col.insert_one({
                "order_id": order_id,
                "store_id": store_id,
                "user_id": buyer_id,
                "status": 1,
                "price": total_price
            })
            result = self.conn.order_col.delete_one({"order_id": order_id, "status": 0})
            if result.deleted_count == 0:
                return error.error_invalid_order_id(order_id)
        except BaseException as e:
            return 528, "{}".format(str(e))
        return 200, "ok"


    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            result = self.conn.user_col.find_one({"user_id": user_id})
            if result is None:
                return error.error_authorization_fail()
            if result.get("password") != password:
                return error.error_authorization_fail()

            result = self.conn.user_col.update_one({"user_id": user_id}, {"$inc": {"balance": add_value}})
            if result.matched_count == 0:
                return error.error_non_exist_user_id(user_id)
        except BaseException as e:
            return 528, "{}".format(str(e))

        return 200, ""

    def receive_books(self, user_id: str, order_id: str) -> (int, str):
        try :
            result = self.conn.order_col.find_one({
                "$or": [
                    {"order_id": order_id, "status": 1},
                    {"order_id": order_id, "status": 2},
                    {"order_id": order_id, "status": 3},
                ]
            })
            if result == None:
                return error.error_invalid_order_id(order_id)
            buyer_id = result.get("user_id")
            paid_status = result.get("status")

            if buyer_id != user_id:
                return error.error_authorization_fail()
            if paid_status == 1:
                return error.error_books_not_sent()
            if paid_status == 3:
                return error.error_books_duplicate_receive()

            self.conn.order_col.update_one({"order_id": order_id}, {"$set": {"status": 3}})
        except BaseException as e:
            return 528, "{}".format(str(e))
        return 200, "ok"


    def search(self, keyword, scope=None, store_id=None, page=1, per_page=10):
        try:
            base_query = {"$text": {"$search": keyword}}
            scope_fields = {
                "title": "title",
                "tags": "tags",
                "book_intro": "book_intro",
                "content": "content"
            }
            query = base_query
            if store_id:
                results = self.conn.store_col.find({"store_id": store_id}, {"books.book_id": 1, "_id": 0})
                for result in results:
                    print(result)
                books_id = [i["book_id"] for i in results["books"]]
                query["id"] = {"$in": books_id}

            results = self.conn.book_col.find(query,
                                              {"score": {"$meta": "textScore"}, "_id": 0, "picture": 0}).sort(
                [("score", {"$meta": "textScore"})])
            # Perform pagination
            results.skip((int(page) - 1) * per_page).limit(per_page)
        except BaseException as e:
            return 530, f"{str(e)}"
        return 200, list(results)
