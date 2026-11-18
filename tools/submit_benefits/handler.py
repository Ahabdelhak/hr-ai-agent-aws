"""Gateway Lambda target: file a benefits claim."""
import json
import logging
import os
from decimal import Decimal

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
    fields = {k: event.get(k) for k in ("employee_name", "benefit_type", "claim_amount")}
    missing = [k for k, v in fields.items() if v in (None, "")]
    if missing:
        return {"status": "error", "message": f"Missing required fields: {', '.join(missing)}"}
    try:
        amount = Decimal(str(fields["claim_amount"]))
    except Exception:
        return {"status": "error", "message": "claim_amount must be a number"}
    if amount <= 0:
        return {"status": "error", "message": "claim_amount must be positive"}
    fields["claim_amount"] = amount
    table().put_item(Item=fields)
    return {"status": "ok", "message": f"Benefits claim for {fields['employee_name']}, {fields['benefit_type']}, {amount} submitted."}
