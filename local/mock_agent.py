"""Run the HR agent locally, no AWS. Keyword routing stands in for the model; mock_kb stands in for hrKnowledgeBase."""
import re
import sys

from mock_kb import answer as kb_answer

LEAVE, BENEFITS = [], []  # stand-ins for the two DynamoDB tables


def submit_leave(employee_name, startDate, endDate):
    missing = [k for k, v in dict(employee_name=employee_name, startDate=startDate, endDate=endDate).items() if not v]
    if missing:
        return f"Missing: {', '.join(missing)}"
    LEAVE.append(dict(employee_name=employee_name, startDate=startDate, endDate=endDate))
    return f"Leave request for {employee_name} from {startDate} to {endDate} submitted."


def submit_benefits(employee_name, benefit_type, claim_amount):
    BENEFITS.append(dict(employee_name=employee_name, benefit_type=benefit_type, claim_amount=claim_amount))
    return f"Benefits claim for {employee_name}, {benefit_type}, ${claim_amount:g} submitted."


def route(prompt):
    p = prompt.lower()
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", prompt)
    name = re.search(r"for ([A-Z][a-z]+ [A-Z][a-z]+)", prompt)
    if "leave" in p and name and len(dates) == 2:
        return submit_leave(name.group(1), dates[0], dates[1])
    amount = re.search(r"\$(\d+(?:\.\d+)?)", prompt)
    if "benefit" in p and name and amount:
        kind = "medical" if "medical" in p else "other"
        return submit_benefits(name.group(1), kind, float(amount.group(1)))
    return kb_answer(prompt)  # anything else is treated as a policy question (hrKnowledgeBase)


if __name__ == "__main__":
    print(route(" ".join(sys.argv[1:]) or "Submit a leave request for John Smith, starting 2026-07-15 and ending 2026-07-18."))
