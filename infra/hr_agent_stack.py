"""Tool layer of hr-ai-agent-aws: two Lambda tools behind an AgentCore Gateway, plus a Bedrock Guardrail.

Not included yet: the Knowledge Base target and the AgentCore Runtime (agent code). See README "Next".
"""
from pathlib import Path

from aws_cdk import CfnOutput, RemovalPolicy, Stack, Duration
from aws_cdk import aws_bedrock as bedrock
from aws_cdk import aws_bedrockagentcore as agentcore
from aws_cdk import aws_dynamodb as ddb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from constructs import Construct

ROOT = Path(__file__).resolve().parents[1]


class HrAgentStack(Stack):
    def __init__(self, scope: Construct, cid: str, **kw) -> None:
        super().__init__(scope, cid, **kw)

        # Demo stack: everything is destroyed with `cdk destroy`.
        vacation = ddb.Table(self, "VacationTable", partition_key=ddb.Attribute(name="employee_name", type=ddb.AttributeType.STRING),
                             billing_mode=ddb.BillingMode.PAY_PER_REQUEST, removal_policy=RemovalPolicy.DESTROY)
        benefits = ddb.Table(self, "BenefitsTable", partition_key=ddb.Attribute(name="employee_name", type=ddb.AttributeType.STRING),
                             billing_mode=ddb.BillingMode.PAY_PER_REQUEST, removal_policy=RemovalPolicy.DESTROY)

        def tool_fn(name: str, table: ddb.Table) -> _lambda.Function:
            fn = _lambda.Function(self, f"{name}Fn", runtime=_lambda.Runtime.PYTHON_3_13, handler="handler.lambda_handler",
                                  code=_lambda.Code.from_asset(str(ROOT / "tools" / name)), timeout=Duration.seconds(10),
                                  environment={"TABLE_NAME": table.table_name})
            table.grant_write_data(fn)
            return fn

        leave_fn = tool_fn("submit_leave", vacation)
        benefits_fn = tool_fn("submit_benefits", benefits)

        # Tool schemas live in S3; the gateway reads them to describe each tool to the model.
        schema_bucket = s3.Bucket(self, "SchemaBucket", removal_policy=RemovalPolicy.DESTROY, auto_delete_objects=True,
                                  block_public_access=s3.BlockPublicAccess.BLOCK_ALL, enforce_ssl=True)
        schemas = s3deploy.BucketDeployment(self, "Schemas", destination_bucket=schema_bucket, destination_key_prefix="schema",
                                            sources=[s3deploy.Source.asset(str(ROOT / "tools" / "schemas"))])

        gw_role = iam.Role(self, "GatewayRole", assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"))
        leave_fn.grant_invoke(gw_role)
        benefits_fn.grant_invoke(gw_role)
        schema_bucket.grant_read(gw_role)

        gateway = agentcore.CfnGateway(self, "Gateway", name="hr-assistant-gateway", role_arn=gw_role.role_arn,
                                       authorizer_type="AWS_IAM", protocol_type="MCP",
                                       description="MCP gateway for HR tools")

        def lambda_target(cid_: str, name: str, fn: _lambda.Function, schema_key: str) -> agentcore.CfnGatewayTarget:
            t = agentcore.CfnGatewayTarget(
                self, cid_, name=name, gateway_identifier=gateway.attr_gateway_identifier,
                target_configuration=agentcore.CfnGatewayTarget.TargetConfigurationProperty(
                    mcp=agentcore.CfnGatewayTarget.McpTargetConfigurationProperty(
                        lambda_=agentcore.CfnGatewayTarget.McpLambdaTargetConfigurationProperty(
                            lambda_arn=fn.function_arn,
                            tool_schema=agentcore.CfnGatewayTarget.ToolSchemaProperty(
                                s3=agentcore.CfnGatewayTarget.S3ConfigurationProperty(
                                    uri=f"s3://{schema_bucket.bucket_name}/schema/{schema_key}"))))),
                credential_provider_configurations=[
                    agentcore.CfnGatewayTarget.CredentialProviderConfigurationProperty(credential_provider_type="GATEWAY_IAM_ROLE")])
            t.node.add_dependency(schemas)
            t.node.add_dependency(gw_role)
            return t

        lambda_target("SubmitLeaveTarget", "submitLeave", leave_fn, "submit_leave.json")
        lambda_target("SubmitBenefitsTarget", "submitBenefits", benefits_fn, "submit_benefits.json")

        # Guardrail: block investment/legal advice, mask basic PII.
        guardrail = bedrock.CfnGuardrail(
            self, "HrGuardrail", name="hr-guardrails",
            blocked_input_messaging="Sorry, I can't help with that topic. Please contact HR directly.",
            blocked_outputs_messaging="Sorry, I can't share that. Please contact HR directly.",
            topic_policy_config=bedrock.CfnGuardrail.TopicPolicyConfigProperty(topics_config=[
                bedrock.CfnGuardrail.TopicConfigProperty(
                    name="LegalAdvice", type="DENY",
                    definition="Providing legal opinions or advice about employment disputes, contracts or lawsuits.",
                    examples=["Can I sue my employer?", "Is my contract legally enforceable?"]),
                bedrock.CfnGuardrail.TopicConfigProperty(
                    name="InvestmentAdvice", type="DENY",
                    definition="Recommending where to invest money, stocks, funds or other financial products.",
                    examples=["Where should I invest my bonus?"])]),
            sensitive_information_policy_config=bedrock.CfnGuardrail.SensitiveInformationPolicyConfigProperty(pii_entities_config=[
                bedrock.CfnGuardrail.PiiEntityConfigProperty(type="CREDIT_DEBIT_CARD_NUMBER", action="BLOCK"),
                bedrock.CfnGuardrail.PiiEntityConfigProperty(type="EMAIL", action="ANONYMIZE")]))
        bedrock.CfnGuardrailVersion(self, "HrGuardrailV1", guardrail_identifier=guardrail.attr_guardrail_id)

        CfnOutput(self, "GatewayId", value=gateway.attr_gateway_identifier)
        CfnOutput(self, "GuardrailId", value=guardrail.attr_guardrail_id)
