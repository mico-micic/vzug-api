from flask import Flask, request, Response

from vzug.const import (QUERY_PARAM_COMMAND, QUERY_PARAM_VALUE, COMMAND_GET_STATUS, COMMAND_GET_MODEL_DESC,
                        COMMAND_GET_PROGRAM, COMMAND_GET_MACHINE_TYPE, ENDPOINT_AI, ENDPOINT_HH, COMMAND_GET_COMMAND,
                        DEVICE_TYPE_SHORT_DISHWASHER)
from util import get_response_from_file_raw

app = Flask(__name__)

def bad_request():
    return Response("{'error':'bad request'}", status=400, mimetype='application/json')


@app.route(f"/{ENDPOINT_AI}", methods=['GET'])
def get_device_status():
    cmd = request.args.get(QUERY_PARAM_COMMAND, "")
    if COMMAND_GET_STATUS in cmd:
        return Response(get_response_from_file_raw("dishwasher_status_timed_resp.json"), mimetype='application/json')
    elif COMMAND_GET_MODEL_DESC in cmd:
        return "AdoraDish V4000"
    else:
        return bad_request()


@app.route(f"/{ENDPOINT_HH}", methods=['GET'])
def get_program():
    cmd = request.args.get(QUERY_PARAM_COMMAND, "")
    val = request.args.get(QUERY_PARAM_VALUE, "")
    if COMMAND_GET_PROGRAM in cmd:
        return Response(get_response_from_file_raw("dishwasher_program_status_timed.json"), mimetype='application/json')
    if cmd == COMMAND_GET_MACHINE_TYPE:
        return DEVICE_TYPE_SHORT_DISHWASHER
    else:
        return bad_request()


if __name__ == '__main__':
    app.run(host="0.0.0.0")
