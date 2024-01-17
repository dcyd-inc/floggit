from datetime import datetime as dt
import functools
import inspect
import json
import logging
import os 
import sys 
import traceback

from flask import request
import networkx as nx



if os.environ.get("NO_GOOGLE_LOGGING"):
    class LocalFormatter(logging.Formatter):
        def format(self, record):
            tb = traceback.format_exc() if record.__dict__.get('exc_info') is not None else ''
            if 'json_fields' in record.__dict__:
                string = str(record.msg)
                for k,v in record.__dict__['json_fields'].items():
                    string += f"\n - {k}: {v}"
                string += "\n"
            else:
                string = super().format(record)
            return string + tb

    hnd = logging.StreamHandler(sys.stdout)
    hnd.setFormatter(LocalFormatter())
    logging.root.addHandler(hnd)
    logging.root.setLevel(logging.INFO)
else:
    from google.cloud.logging import Client
    client = Client()
    client.setup_logging()
    logging.root.setLevel(logging.INFO)


def flog(function=None, is_route=False):
    """Decorate a client's function."""
    def decorate(function: callable):
        function_signature = inspect.signature(function)

        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            f = f"{function.__module__}.{function.__name__}"
            # Log call of client's function
            if is_route:
                request_payload = request.args \
                        if request.method == 'GET' else request.json
            else:
                request_payload = bind_function_arguments(
                        signature=function_signature, args=args, kwargs=kwargs)
            logging.info(f'> {f}', extra={
                'json_fields': jsonify_payload(request_payload),
                'labels': {
                    'monitor': {
                        'event_type': 'request',
                        'function': f,
                        'matchstr': (ms:=get_random_string())
                    }
                }
            })
            # Call client's function
            start_ts = dt.now()
            response = function(*args, **kwargs)
            end_ts = dt.now()

            logging.info(f'< {f}', extra={
                'json_fields': {'response': jsonify_payload(response)},
                'labels': {
                    'monitor': {
                        'event_type': 'response',
                        'function': f,
                        'matchstr': ms,
                        'run_time': str(end_ts - start_ts)
                    }
                }
            })

            return response
        return wrapper
    if function:
        return decorate(function)
    return decorate


def jsonify_payload(payload): 
    if isinstance(payload, dict):
        j = {}
        for k,v in payload.items():
            try:
                json.dumps({k:1})
            except:
                key = repr(k)
            else:
                key = k
            j[key] = jsonify_payload(v)
        return j
    elif isinstance(payload, (tuple, list)):
        j = []
        for i in payload:
            j.append(jsonify_payload(i))
        return j if isinstance(payload, list) else tuple(j)
    elif type(payload).__name__ == 'Response':
        return jsonify_payload(payload.get_json())
    elif type(payload).__name__ in ['DataFrame', 'Series']:
        return payload.head().to_json(
                orient='split', default_handler=str, date_format='iso')
    elif type(payload).__name__ == 'Graph':
        return json.dumps(nx.node_link_data(payload))
    elif type(payload).__name__ == 'set':
        return jsonify_payload(list(payload))
    else: # non-Response atomic type
        try:
            return jsonify_payload(dict(payload))
        except:
            try:
                return json.dumps(payload)
            except:
                return f'Not jsonifiable: {repr(payload)}'


def get_random_string(n=10):
    import string, random

    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))


def bind_function_arguments(*, signature, args, kwargs):
    ba = signature.bind(*args, **kwargs)
    ba.apply_defaults()
    return ba.arguments
