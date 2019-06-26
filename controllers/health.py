import json

class HealthPage(object):

    @classmethod
    def check(cls):
        return json.dumps({'status': 'ok'})
