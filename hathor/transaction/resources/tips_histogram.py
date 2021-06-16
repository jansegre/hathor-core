# Copyright 2021 Hathor Labs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from structlog import get_logger
from twisted.web import resource

from hathor.api_util import parse_get_arguments, set_cors

ARGS = ['begin', 'end']

logger = get_logger()


# XXX: this resource is DEPRECATED and will be removed soon
class TipsHistogramResource(resource.Resource):
    """ Implements a web server API to return the tips in a timestamp interval.
        Returns a list of timestamps and numbers of tips.

    You must run with option `--status <PORT>`.
    """
    isLeaf = True

    def __init__(self, manager):
        self.manager = manager
        self.log = logger.new()

    def render_GET(self, request):
        """ Get request to /tips-histogram/ that return the number of tips between two timestamp
            We expect two GET parameters: 'begin' and 'end'

            'begin': int that indicates the beginning of the interval
            'end': int that indicates the end of the interval

            :rtype: string (json)
        """
        self.log.warn('DEPRECATED: this resource doesn\'t work anymore and will be removed soon')
        request.setHeader(b'content-type', b'application/json; charset=utf-8')
        set_cors(request, 'GET')

        parsed = parse_get_arguments(request.args, ARGS)
        if not parsed['success']:
            return json.dumps({
                'success': False,
                'message': 'Missing parameter: {}'.format(parsed['missing'])
            }).encode('utf-8')

        args = parsed['args']

        # Get quantity for each
        try:
            begin = int(args['begin'])
        except ValueError:
            return json.dumps({
                'success': False,
                'message': 'Invalid parameter, cannot convert to int: begin'
            }).encode('utf-8')

        try:
            end = int(args['end'])
        except ValueError:
            return json.dumps({
                'success': False,
                'message': 'Invalid parameter, cannot convert to int: end'
            }).encode('utf-8')

        v = []
        for timestamp in range(begin, end + 1):
            # tx_tips = self.manager.tx_storage.get_tx_tips(timestamp)
            # XXX: this new histogram is definitely broken as it only considers the current mempool,
            #      but it is now deprecated so it isn't a problem
            tx_tips = self.manager.generate_parent_txs(timestamp).get_all_tips()
            v.append((timestamp, len(tx_tips)))

        return json.dumps({'success': True, 'tips': v}).encode('utf-8')
