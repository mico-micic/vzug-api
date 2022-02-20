from flask import Flask, request, Response

from vzug.const import (QUERY_PARAM_COMMAND, QUERY_PARAM_VALUE, COMMAND_GET_STATUS, COMMAND_GET_MODEL_DESC,
                        COMMAND_GET_PROGRAM, COMMAND_GET_MACHINE_TYPE, ENDPOINT_AI, ENDPOINT_HH, COMMAND_GET_COMMAND,
                        DEVICE_TYPE_SHORT_DRYER)
from util import get_response_from_file_raw

app = Flask(__name__)

CMD_VALUE_CONSUMP_DRYER_TOTAL = 'TotalXconsumptionXdrumDry'
CMD_VALUE_CONSUMP_DRYER_AVG = 'AverageXperXcycleXdrumDry'


def bad_request():
    return Response("{'error':'bad request'}", status=400, mimetype='application/json')


@app.route(f"/{ENDPOINT_AI}", methods=['GET'])
def get_device_status():
    cmd = request.args.get(QUERY_PARAM_COMMAND, "")
    if COMMAND_GET_STATUS in cmd:
        return Response(get_response_from_file_raw("dryer_status_ok_resp.json"), mimetype='application/json')
    elif COMMAND_GET_MODEL_DESC in cmd:
        return "AdoraDry V4000"
    else:
        return bad_request()


@app.route(f"/{ENDPOINT_HH}", methods=['GET'])
def get_program():
    cmd = request.args.get(QUERY_PARAM_COMMAND, "")
    val = request.args.get(QUERY_PARAM_VALUE, "")
    if COMMAND_GET_PROGRAM in cmd:
        return Response(get_response_from_file_raw("dryer_program_status_active.json"), mimetype='application/json')
    if COMMAND_GET_COMMAND in cmd and val in CMD_VALUE_CONSUMP_DRYER_TOTAL:
        return Response(get_response_from_file_raw("dryer_consumption_total.json"), mimetype='application/json')
    if COMMAND_GET_COMMAND in cmd and val in CMD_VALUE_CONSUMP_DRYER_AVG:
        return Response(get_response_from_file_raw("dryer_consumption_avg.json"), mimetype='application/json')
    if cmd == COMMAND_GET_MACHINE_TYPE:
        return DEVICE_TYPE_SHORT_DRYER
    else:
        return bad_request()


if __name__ == '__main__':
    app.run(host="0.0.0.0")
