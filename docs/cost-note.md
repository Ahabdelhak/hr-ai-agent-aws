# Cost note

Goal: build, test, and tear down for close to nothing. Verify current prices on the AWS pricing pages before deploying; numbers change.

## Cheap by design
- **Lambda, DynamoDB, S3:** negligible at demo volume.
- **Model:** a small on-demand model, short prompts, few test runs.

## Where money leaks
- **Vector store:** OpenSearch Serverless has a standing monthly floor. Avoid it; use a Managed KB or S3 Vectors.
- **Load balancer:** bills while it exists. Destroy it after demos.
- **AgentCore Runtime / gateway:** switch off between sessions.

## Rules
1. New or clean AWS account; check the current free-tier and credit terms.
2. AWS Budgets alert at $5 and $10 before deploying anything.
3. Deploy with IaC, test for about an hour, then `cdk destroy`.
4. Keep proof in the repo (screenshots), not a running system.

## Per-session checklist
- [ ] Budget alerts on
- [ ] Region chosen, cheapest model selected
- [ ] Stack destroyed
- [ ] Billing page checked the next day
