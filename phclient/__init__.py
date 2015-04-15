# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import requests

class SignatureList(object):

    def __init__(self, signatures):
        self.signatures = signatures

    def __len__(self):
        return len(self.signatures)

    def filter(self, *args):
        filtered_signatures = {}
        for (signature, signature_value) in self.signatures.iteritems():
            skip = False
            for (key, val) in args:
                if signature_value.get(key) != val:
                    skip = True
                    break
            if not skip:
                filtered_signatures[signature] = signature_value
        return SignatureList(filtered_signatures)

    def get_signature_hashes(self):
        return self.signatures.keys()

    def get_property_names(self):
        property_names = set()
        for signature_value in self.signatures.values():
            for property_name in signature_value.keys():
                property_names.add(property_name)
        return property_names

    def get_property_values(self, property_name):
        property_values = set()
        for signature_value in self.signatures.values():
            if signature_value.get(property_name):
                property_values.add(signature_value[property_name])
        return property_values

class Series(object):
    def __init__(self, blob):
        self.blob = blob

    def __getitem__(self, key):
        return map(lambda el: el[key], self.blob)

class TimeInterval(object):
    DAY = 86400
    WEEK = 604800
    TWO_WEEKS = 1209600
    SIXTY_DAYS = 5184000
    NINETY_DAYS = 7776000

class Client(object):

    PERFORMANCE_SERIES_SUMMARY_ENDPOINT = '/api/project/%s/performance-data/0/get_performance_series_summary/?interval=%s'
    SIGNATURE_PROPERTIES_ENDPOINT = '/api/project/%s/performance-data/0/get_signature_properties/?signatures=%s'
    PERFORMANCE_DATA_ENDPOINT = '/api/project/%s/performance-data/0/get_performance_data/?interval_seconds=%s'
    RESULT_SET_ENDPOINT = '/api/project/%s/resultset/%s/'

    def __init__(self, server="https://treeherder.mozilla.org"):
        self.server = server

    def get_signatures(self, project_name, time_interval = TimeInterval.WEEK):
        r = requests.get(self.server + self.PERFORMANCE_SERIES_SUMMARY_ENDPOINT % (project_name, time_interval))
        return SignatureList(r.json())

    def get_signature_properties(self, project_name, signature):
        r = requests.get(self.server + self.SIGNATURE_PROPERTIES_ENDPOINT % (project_name, signature))
        return r.json()[0]

    def get_series_list(self, project_name, signature_list, time_interval=TimeInterval.WEEK):
        url = (self.server + self.PERFORMANCE_DATA_ENDPOINT % (project_name, time_interval))
        for signature in signature_list:
            url += '&signatures=%s' % signature
        r = requests.get(url)
        result_map = {}
        for dict in r.json():
            result_map[dict['series_signature']] = dict['blob']

        return [Series(result_map[signature]) for signature in signature_list]

    def get_series(self, project_name, signature, time_interval=TimeInterval.WEEK):
        return self.get_series_list(project_name, [signature],
                                    time_interval=time_interval)[0]

    def get_revision(self, project_name, result_set_id):
        r = requests.get(self.server + self.RESULT_SET_ENDPOINT % (
            project_name, result_set_id))

        return r.json()['revisions'][0]['revision']
