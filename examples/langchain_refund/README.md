# LangChain refund agent

A standalone synthetic refund assistant built with LangChain's `create_agent`. Its only tool is a read-only eligibility lookup over fictional orders. It cannot issue a refund. This example does not change the existing hosted agent or its dependencies.

With Python 3.10+ and the dependencies in `examples\langchain_refund\requirements.txt` installed from your approved package source, run these commands from the repository root:

```powershell
python examples\langchain_refund\refund_agent.py --order-id demo-1002
python examples\langchain_refund\refund_agent.py --order-id demo-1002 --prompt examples\langchain_refund\refund-candidate.txt
```

In scripted mode the baseline answers without checking; the candidate executes `check_refund_eligibility` and denies the ineligible order. The CLI reports tool calls and the final answer as JSON. No model credentials or network calls are needed in this mode. This demonstrates the tool loop, not measured improvement on a hosted model.

To use a live tool-capable model, set `OPENAI_BASE_URL` and `OPENAI_API_KEY` through your local configuration, then add `--model <deployment>`. This sends the chosen prompt and synthetic conversation to that endpoint.

For a Draft PR optimization demo, keep `prompts/refund.txt` at the repository root. A local runner can import `run_refund_agent` from a trusted checkout and pass it the prompt read at each candidate commit SHA. Do not fetch or execute Python from candidate commits.

To link this local runtime to [a Foundry external agent](https://learn.microsoft.com/azure/foundry/agents/how-to/register-external-agent), export `invoke_agent` spans to the Application Insights resource connected to your Foundry project. Register the same OpenTelemetry ID as the one your runner sets on `gen_ai.agent.id`. This links telemetry; it does not expose a local endpoint or let Foundry invoke the agent.
