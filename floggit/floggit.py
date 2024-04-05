from datetime import datetime as dt
import functools
import inspect
import json
import os 
from . utils import get_random_string
from flask import request
import networkx as nx

TRACE_ID = get_random_string(n=20)

if os.environ.get("NO_GOOGLE_LOGGING"):
    import logging, sys, traceback

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

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(LocalFormatter())
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    def _log(payload, **kw):
        logger.info(
                payload.get('message', ''),
                extra={'json_fields': payload}
        )
else:
    import google.cloud.logging
    client = google.cloud.logging.Client()
    logger = client.logger('floggit')

    def _log(payload, **kw):
        logger.log_struct(payload, **kw)


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
            _log(
                {
                    'message': f'> {f}',
                    'args': jsonify_payload(request_payload),
                    'module': function.__module__,
                    'function_name': function.__name__,
                    'request_id': (ms:=get_random_string())
                },
                severity="INFO",
                trace=TRACE_ID
            )

            # Call client's function
            start_ts = dt.now()
            response = function(*args, **kwargs)
            end_ts = dt.now()

            _log(
                {
                    'message': f'< {f}',
                    'response': jsonify_payload(response),
                    'request_id': ms,
                    'run_time': str(end_ts - start_ts)
                },
                severity="INFO",
                trace=TRACE_ID
            )

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
    elif type(payload).__name__ == 'ndarray':
        return jsonify_payload(payload.tolist())
    elif type(payload).__name__ in ['tuple', 'list']:
        return [jsonify_payload(i) for i in payload]
    elif type(payload).__name__ == 'Response':
        return jsonify_payload(payload.get_json())
    elif type(payload).__name__ in ['DataFrame', 'Series']:
        return payload.head().to_json(
                orient='split', default_handler=str, date_format='iso')
    elif isinstance(payload, nx.Graph):
        return jsonify_payload(nx.node_link_data(payload))
    elif type(payload).__name__ == 'set':
        return jsonify_payload(list(payload))
    else: # atomic
        try:
            return json.dumps(payload)
        except:
            return f'Not jsonifiable: {repr(payload)}'


def bind_function_arguments(*, signature, args, kwargs):
    ba = signature.bind(*args, **kwargs)
    ba.apply_defaults()
    return ba.arguments
