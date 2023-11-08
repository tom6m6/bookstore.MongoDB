from pymongo import MongoClient
import random
import base64
import pymongo

class Book:
    id: str
    title: str
    author: str
    publisher: str
    original_title: str
    translator: str
    pub_year: str
    pages: int
    price: int
    binding: str
    isbn: str
    author_intro: str
    book_intro: str
    content: str
    tags: [str]
    pictures: [bytes]

    def __init__(self):
        self.tags = []
        self.pictures = []


class BookDB:
    def __init__(self, large: bool = False):
        self.host = '127.0.0.1'
        self.port = 27017
        self.client = pymongo.MongoClient(self.host, self.port)
        self.db = self.client['bookstore']
        self.book_col = self.db['books']

    def get_book_count(self):
        users_col = self.db.books
        result = users_col.count_documents({})
        return result

    def get_book_info(self, start, size) -> [Book]:
        books = []
        users_col = self.db.books
        cursor = users_col.find().sort("book_id", pymongo.ASCENDING).skip(start).limit(size)
        for doc in cursor:
            book = Book()
            book.id = doc['id']
            book.title= doc['title']
            book.author = doc['author']
            book.publisher = doc['publisher']
            book.original_title = doc['original_title']
            book.translator = doc['translator']
            book.pub_year = doc['pub_year']
            book.pages = doc['pages']
            book.price = doc['price']

            book.currency_unit = doc['currency_unit']
            book.binding = doc['binding']
            book.isbn = doc['isbn']
            book.author_intro = doc['author_intro']
            book.book_intro = doc['book_intro']
            book.content = doc['content']
            picture = doc['picture']
            tags = doc['tags']

            for tag in tags.split("\n"):
                if tag.strip() != "":
                    book.tags.append(tag)
            for i in range(0, random.randint(0, 9)):
                if picture is not None:
                    encode_str = base64.b64encode(picture).decode("utf-8")
                    book.pictures.append(encode_str)
            books.append(book)

        return books