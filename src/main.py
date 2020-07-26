#!/usr/bin/python
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# -*- coding: utf-8 -*-
import logging

from functools import wraps

from flask import Flask, json, jsonify, request
from werkzeug.exceptions import (BadRequest, HTTPException,
                                InternalServerError)

from flask_cors import CORS
from models.dictionary_tree import DictionaryTree, DictionaryTreeException



tree = DictionaryTree()

try:
    tree.deserialize("./third_party/tla_lemma_glyph_dict.json")
except DictionaryTreeException as e:
    print("Error:", e)
    tree = None


# Define a new get_headers() function for the HTTPException class,
# to return application/json MIME type rather than plain HTML
# @TODO Review how this is being done and implement in a more
# pythoninc way
def get_headers(self, environ=None):
    return [('Content-Type', 'application/json')]


HTTPException.get_headers = get_headers


# Define a new get_body() function for the HTTPException class,
# to return json rather than plain HTML
# @TODO Review how this is being done and implement in a more pythoninc way
def get_body(self, environ=None):
    return json.dumps({
        'success': False,
        'message': self.description,
        'code': self.code
    })


HTTPException.get_body = get_body


# Create a wrapper for ensuring API requests have an application/JSON MIME type,
# raising a custom BadRequest if they don't
# @TODO Review whether there is a better way to implement this.
# A decorator seems like the most sensible, but mayber there is a better way?
def require_json(params=None):
    '''Decorator function to wrap app route functions when we explicity want
    the Content_Type to be application/json. Checks the request.is_json
    and raises a BadRequest exception if not. Also allows for a list of
    required parameters and checks for their existence, rasing a BadRequest if
    any of them are missing.'''
    params = params or []
    def require_json_inner(func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            if request.is_json:

                json_payload = request.get_json(cache=False)
                for param in params:
                    if not json_payload.get(param):
                        raise BadRequest(
                            'The request is missing the {} parameter'.format(
                                param))

                return func(json_payload, *args, **kwargs)

            raise BadRequest(
                'The request content type must be application/json')

        return func_wrapper

    return require_json_inner


app = Flask(__name__)
CORS(app)


@app.route('/translation', methods=['POST'])
@require_json(['sequence'])
def classification(payload):
    sequence = payload.get('sequence')
    if not isinstance(sequence, list):
        raise BadRequest("Unable to process sequence {}".format(
            payload.get('sequence')))

    try:
        entries = tree.get_entries_in_sequence(sequence)
        responses = []
        for entry in entries:
            response_dict = {}
            start, end = entry[0]
            response_dict['start'] = start
            response_dict['end'] = end

            sequence = entry[2]['word']
            response_dict['sequence'] = sequence

            translations = []
            for key, value in entry[2]['translations'].items():
                print(key, value)
                if key == 'transliteration':
                    response_dict['transliteration'] = value
                else:
                    translations_dict = {'locale': key, 'translation': value}
                    translations.append(translations_dict)
            response_dict['translations'] = translations
            responses.append(response_dict)

        return jsonify(code=200, success=True, result=responses)

    except Exception as e:
        logging.error(e)
        raise InternalServerError('Something went wrong!')
