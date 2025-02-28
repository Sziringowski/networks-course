import json
import uuid
import os
from flask import Flask, request, jsonify, abort, send_from_directory
from flask_dropzone import Dropzone

from pathlib import Path

app = Flask(__name__)

path_upload = 'uploads'
app.config['DROPZONE_UPLOAD_MULTIPLE'] = False
app.config['DROPZONE_ALLOWED_FILE_TYPE'] = 'image'
app.config['DROPZONE_MAX_FILE_SIZE'] = 3  # макс размер файла (МБ)
app.config['DROPZONE_UPLOAD_PATH'] = path_upload # куда складываем

dropzone = Dropzone(app)

os.makedirs(app.config['DROPZONE_UPLOAD_PATH'], exist_ok=True) # чек, что папка загрузки существует

'''
структура датабазы:
{
    'id': {
    'name': '',
    'description': '',
    'icon': ''
    }
}

<product-json>:
{
    "id": '',
    "name": '',
    "description": '',
    "icon": ''
}
'''

doc_keys = ["id", "name", "description", "icon"] # допустимые json ключи в датабазе

products = {} # database with products

# main page
@app.route('/')
def index():
    return 'lab02, Shiringovskiy'

# put item
@app.route('/product', methods=['POST'])
def post_data():

    input = request.get_json()

    if (input is None) or (not all(key in doc_keys for key in input.keys())): # запрещаем добавлять сомнительные свойства объекту
        abort(400) # некорректный ввод
    
    key = str(uuid.uuid4()) # генерим айди. можно было просто key = len(dict), нумерация с 0

    item = {
        "id": key,
        "name": input["name"],
        "description": input["description"],
        "icon": '' # мы не предусматриваем на текущем этапе возможность подгрузить картинку, поэтому создаётся по дефолту с пустым имаджем, а если это и произойдёт, то мы просто оставим атрибут пустым
        } # определяем айтем

    products[item["id"]] = {
        "name": item["name"],
        "description": item["description"],
        "icon": ''
        } # записываем в датабазу

    return jsonify(item) # возвращаем <product-json> с автогенированным случайным ключом 

# get item
@app.route('/product/<product_id>', methods=['GET'])
def get_product(product_id):

    product_id = str(product_id)

    if not(product_id in list(products.keys())):
        abort(404) # нет айтема
    
    product = products[product_id] # нашли, присвоили

    item = {
        "id": product_id,
        "name": product["name"],
        "description": product["description"],
        "icon": product["icon"] # здесь уже корректного вида продукт в ДБ => сущ icon
    } # распарсили айтем

    return jsonify(item)

# put (upd) item
@app.route('/product/<product_id>', methods=['PUT'])
def update_data(product_id):
    
    if not(product_id in list(products.keys())):
        abort(404) # нет айтема
    
    input = request.get_json()

    if (input is None) or ("icon" in list(input.keys())) or (not all(key in doc_keys for key in input.keys())): # отслеживаем, чтобы на этом этапе юзер не просунул имадж и сомнительные свойства
        abort(400) # incorrect input
    
    product = products[product_id]

    for key in list(input.keys()):
        product[key] = input[key]

    item = {
        "id": product_id,
        "name": product["name"],
        "description": product["description"],
        "icon": product["icon"]
    }

    return jsonify(item)

# delete item
@app.route('/product/<product_id>', methods=['DELETE'])
def delete_data(product_id):

    if not(product_id in list(products.keys())):
        abort(404) # нет айтема
    
    product = products.pop(product_id) # зафиксировали, что дропнули

    item ={
        "id": product_id,
        "name": product["name"],
        "description": product["description"],
        "icon": product["icon"]
    }

    if os.path.exists(f'{path_upload}/{product_id}_icon.png'):
        os.remove(f'{path_upload}/{product_id}_icon.png') # сносим картинку, если была

    return jsonify(item)

# get all
@app.route('/product', methods=['GET'])
def get_all_items():

    database_array = [
        {
            "id": key,
            "name": products[key]["name"],
            "description": products[key]["description"],
            "icon": products[key]["icon"]
        } for key in list(products.keys())
    ] # transform dict - like database to array

    return jsonify(database_array)

# подгрузка картинок
@app.route('/product/<product_id>/image', methods=['POST'])
def upload_image(product_id):
    if 'icon' not in request.files:
        abort(400)

    file = request.files['icon']
    filename = f"{product_id}_icon.png"  # Уникальное имя файла вида <id>_icon.png
    products[product_id]["icon"] = filename # апдейтим icon

    if file.filename == '':
        abort(400)

    # Сохраняем файл
    file.save(os.path.join(app.config['DROPZONE_UPLOAD_PATH'], filename))
    
    return jsonify({"filename": filename})

# получение картинок
@app.route('/product/<product_id>/image', methods=['GET'])
def get_image(product_id):
    if not(product_id in list(products.keys())):
        abort(404) # нет айтема

    filename = f"{product_id}_icon.png"
    try:
        return send_from_directory(app.config['DROPZONE_UPLOAD_PATH'], filename)
    except FileNotFoundError:
        abort(404)

# определение параметров серва
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
