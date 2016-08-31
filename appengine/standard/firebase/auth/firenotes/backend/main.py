# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START app]
import logging

import firebase_helper
from flask import Flask, jsonify, request
import flask_cors
from google.appengine.ext import ndb


app = Flask(__name__)
flask_cors.CORS(app)


class Note(ndb.Model):
    """NDB model class for a user's note.
    Key is user id from decrypted token."""
    friendly_id = ndb.StringProperty()
    message = ndb.TextProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)


def query_database(user_id):
    """Fetches all notes associated with user_id and orders them
    by date created, with most recent note processed first."""
    ancestor_key = ndb.Key(Note, user_id)
    query = Note.query(ancestor=ancestor_key).order(-Note.created)
    notes = query.fetch()

    note_messages = []

    for note in notes:
        note_messages.append({'friendly_id': note.friendly_id,
                              'message': note.message,
                              'created': note.created})

    return note_messages


@app.route('/notes', methods=['GET'])
def list_notes():
    """Queries database for user's notes to display."""
    claims = firebase_helper.verify_auth_token()
    if not claims:
        return 'Unauthorized', 401

    notes = query_database(claims['sub'])

    return jsonify(notes)


@app.route('/notes', methods=['POST', 'PUT'])
def add_note():
    """
    Adds a note to the user's notebook. The request should be in this format:

        {
            "message": "note message."
        }
    """

    claims = firebase_helper.verify_auth_token()
    if not claims:
        return 'Unauthorized', 401

    data = request.get_json()

    # Populates note properties according to the model,
    # with the user ID as the key.
    note = Note(parent=ndb.Key(Note, claims['sub']),
                message=data['message'])

    # Some providers do not provide one of these so either can be used.
    if 'name' in claims:
        note.friendly_id = claims['name']
    else:
        note.friendly_id = claims['email']

    # Stores note in database.
    note.put()

    return 'OK', 200


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500
# [END app]
