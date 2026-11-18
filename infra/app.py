import aws_cdk as cdk

from hr_agent_stack import HrAgentStack

app = cdk.App()
HrAgentStack(app, "HrAgentAws")
app.synth()
