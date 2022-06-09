from unittest import result
from flask import Flask, request
import json
import psycopg2


app = Flask(__name__)
conn = psycopg2.connect(
    host='localhost',
    dbname='libra',
    user='postgres',
    password='1'
)


class Database:
    def __init__(self):
        self.connection = None
        self.cur = conn.cursor()

    def find_one(self, sql, args):
        self.cur.execute(sql, args)
        return self.cur.fetchone()

    def find_all(self, sql, *kargs):
        self.cur.execute(sql, *kargs)
        return self.cur.fetchall()

    def mutate(self, sql, args):
        self.cur.execute(sql, args)
        conn.commit()


db = Database()


@app.route('/<status>')
def list(status):
    books = db.find_all('select * from books where status = %s', [status])
    return json.dumps(books)


@app.route('/create', methods=['POST'])
def insert():
    data = request.json
    books = [book for book in db.find_all('select * from books where name = %s', (data['name'],))]
    if len(books)!=0:
        return {'msg': 'data existed'}
    db.mutate('insert into books (name, author, status) values (%s, %s, %s)',
                (data['name'], data['author'], data['status']))
    return {'msg': 'book inserted'}


@app.route('/update/books/<id>', methods=['PUT'])
def update(id):
    data = request.json
    book_tuple = db.find_one('select * from books where id = %s''', [id])
    if not book_tuple:
        return {'msg': 'Could not find the book'}

    book_dict = {
        'id': book_tuple[0],
        'name': book_tuple[1],
        'author': book_tuple[2],
        'status': book_tuple[3],
        'cust_id': book_tuple[4]
    }
    book_dict.update(data)
    db.mutate('''update books set name = %s, author = %s, status = %s, cust_id=%s where id = %s''',
                (book_dict['name'], book_dict['author'], book_dict['status'], book_dict['cust_id'], book_dict['id']))
    return {'msg': 'book updated'}


@app.route('/delete/books/<id>', methods=['DELETE'])
def delete(id):
    book_tuple = db.find_one('''select * from books where id = %s''', [id])
    if not book_tuple:
        return {'msg': 'Could not find the book'}
    db.mutate('''delete from books where id = %s''', [id])
    return {'msg': 'book deleted'}


@app.route('/register', methods=['POST'])
def cust_info():
    data = request.json
    db.mutate('''insert into custs (name, bday, phone) values (%s, %s, %s)''',
                (data['name'], data['bday'], data['phone']))
    return {'msg': 'Customer informations has been inserted'}


@app.route('/customers')
def profiles():
    customers = [{
        'id': result[0],
        'name': result[1],
        'birthday': result[2].strftime("%m/%d/%Y"),
        'phone': result[3]
    } for result in db.find_all('select * from custs')]
    return json.dumps(customers)


@app.route('/customers/<id>')
def profile(id):
    customers = [{
        'id': result[0],
        'name': result[1],
        'birthday': result[2].strftime("%m/%d/%Y"),
        'phone': result[3]
    } for result in db.find_all('select * from custs where id=%s', [id])]
    if not len(customers):
        return {'msg': "This customer doesn't exist"}
    return json.dumps(customers)


@app.route('/customers/books/<int:id>')
def cust_books(id):
    rent_list = db.find_all('''select * from books where cust_id = %s''', [id])
    return json.dumps(rent_list)
