import json
import pytest
import uuid
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller



class TestSearch:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.buyer_id = "test_new_search_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = "test_new_search_buyer_id_{}".format(str(uuid.uuid1()))
        self.buyer = register_new_buyer(self.buyer_id, self.password)

        self.user_id = "test_crete_store_user_{}".format(str(uuid.uuid1()))
        self.store_id = "test_create_store_store_{}".format(str(uuid.uuid1()))
        self.password = self.user_id
        self.seller = register_new_seller(self.user_id, self.password)
        code = self.seller.create_store(self.store_id)
        assert code == 200

        self.keyword = "hello"

        self.rs = RequestSearch()
        book_db = book.BookDB()
        self.book_example = book_db.get_book_info(0, 1)[0]

    def test_all_field_search(self):
        content, code = self.buyer.search(self.keyword)
        content = json.loads(content)['message']
        print(content, len(content))
        assert code == 200


