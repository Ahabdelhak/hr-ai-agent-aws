# Decision log

## 1. Gateway targets instead of hard-coded tools
**Choice:** expose the knowledge base and both Lambdas as AgentCore Gateway targets over MCP.
**Why:** the agent code stayed unchanged when I added `submitBenefits`. Capabilities scale by adding targets.
**Trade-off:** one more service to configure and secure.

## 2. Tool schemas in S3, one per Lambda
**Choice:** each Lambda target points to a JSON schema (name, purpose, inputs) in S3.
**Why:** the model chooses tools from these descriptions, so clear schemas drive correct routing.
**Lesson:** a wrong schema path or ARN is the first thing to check when a target fails.

## 3. IAM role for outbound auth
**Choice:** the gateway calls targets with its IAM role.
**Why:** no stored keys or tokens.

## 4. Cheapest model that works
**Choice:** Nova Lite on-demand.
**Why:** the lab's IAM policy blocked the Nova 2 Lite inference profile (403 on `bedrock:InvokeModel`), and a small model is enough for FAQ plus tool calls.

## 5. Vector store (for the portfolio build)
**Choice:** prefer S3 Vectors or a Managed KB over OpenSearch Serverless.
**Why:** OpenSearch Serverless has a standing monthly cost floor that is wrong for a demo.
**Trade-off:** check feature and region support before committing.

## 6. Test path when the UI is unreachable
**Observation:** the Streamlit app behind an HTTP load balancer timed out from my browser, while the load balancer was Active, the target Healthy and port 80 open.
**Decision:** test the same runtime through the AgentCore Test agent console (`{"prompt": "..."}`) so the result is still valid.
**Lesson:** isolate layers (LB, target, security group, client) before blaming the app.
