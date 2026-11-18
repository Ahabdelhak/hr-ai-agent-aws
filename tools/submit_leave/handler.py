"""Gateway Lambda target: file a leave request. The gateway passes tool arguments as the event."""
import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_table = None


def table():
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    return _table


def lambda_handler(event, context):
    logger.info("event: %s", json.dumps(event))
    fields = {k: event.get(k) for k in ("employee_name", "startDate", "endDate")}
    missing = [k for k, v in fields.items() if not v]
    if missing:
        return {"status": "error", "message": f"Missing required fields: {', '.join(missing)}"}
    table().put_item(Item=fields)
    return {"status": "ok", "message": f"Leave request for {fields['employee_name']} from {fields['startDate']} to {fields['endDate']} submitted."}
