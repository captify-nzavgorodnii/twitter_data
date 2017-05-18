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
from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()
import logging

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

from flask import Flask
from flask import jsonify
from flask import request
from flask import make_response

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os


# Flask app should start in global layout
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def hello():
    a = {'name': 'captibot'}
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = makeWebhookResult(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500

def makeWebhookResult(req):
    return {
        "speech": "Hi, I am the backend, this is the name I have received: " + req.get('result').get('parameters').get('given-name'),
        "displayText": "tyest diplay text",
        # "data": data,
        # "contextOut": [],
        "source": "captify bot"
    }

# [END app]
