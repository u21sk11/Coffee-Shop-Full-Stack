import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


@app.after_request
def after_request(response):
    response.headers.add(
        'Access-Control-Allow-Headers',
        'Content-Type,Authorization')
    response.headers.add(
        'Access-Control-Allow-Methods',
        'GET,PATCH,POST,DELETE,OPTIONS')
    return response


db_drop_and_create_all()

# ROUTES
@app.route("/drinks", methods=['GET'])
def get_drinks():
    drinks_formatted = []

    try:
        drinks = Drink.query.all()
        for drink in drinks:
            drinks_formatted.append(drink.short())
    except ConnectionError:
        abort(503)

    data = {
        "success": True,
        "drinks": drinks_formatted
    }

    return jsonify(data)


@app.route("/drinks-detail", methods=['GET'])
@requires_auth("get:drinks-detail")
def get_drinks_details(payload):
    drinks_formatted = []

    try:
        drinks = Drink.query.all()
        for drink in drinks:
            drinks_formatted.append(drink.long())
    except ConnectionError:
        abort(503)

    data = {
        "success": True,
        "drinks": drinks_formatted
    }

    return jsonify(data)


@app.route("/drinks", methods=['POST'])
@requires_auth("post:drinks")
def post_drinks(payload):
    title = request.get_json()['title']
    recipe = str(request.get_json()['recipe'])
    recipe_formatted = recipe.replace("'", '"')

    try:
        new_drink = Drink(title=title, recipe=recipe_formatted)
        new_drink.insert()
    except ConnectionError:
        abort(503)

    data = {
        "success": True,
        "drinks": new_drink.long()
    }

    return jsonify(data)


@app.route("/drinks/<int:drink_id>", methods=['PATCH'])
@requires_auth("patch:drinks")
def patch_drinks(payload, drink_id):
    try:
        found_drink = Drink.query.get(drink_id)
        if found_drink is None:
            abort(404)

        title = request.get_json()['title']
        recipe = str(request.get_json()['recipe'])
        recipe_formatted = recipe.replace("'", '"')

        found_drink.title = title
        found_drink.recipe = recipe_formatted

        found_drink.update()

    except ConnectionError:
        abort(503)

    formatted_drink = []
    formatted_drink.append(found_drink.long())

    data = {
        "success": True,
        "drinks": formatted_drink
    }

    return jsonify(data)


@app.route("/drinks/<int:drink_id>", methods=['DELETE'])
@requires_auth("delete:drinks")
def delete_drinks(payload, drink_id):
    try:
        found_drink = Drink.query.get(drink_id)
        if found_drink is None:
            abort(404)

        found_drink.delete()

    except ConnectionError:
        abort(503)

    data = {
        "success": True,
        "delete": found_drink.id
    }

    return jsonify(data)

# Error Handling
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False,
                    "error": 422,
                    "message": "unprocessable"
                    }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404


@app.errorhandler(503)
def network_error(error):
    return jsonify({
                    "success": False,
                    "error": 503,
                    "message": "issues communicating with the database"
                    }), 503


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response
