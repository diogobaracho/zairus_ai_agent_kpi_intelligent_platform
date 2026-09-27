# Documentation

| If you want to… | Go to |
|---|---|
| Run the stack in 10 minutes | [how-to/run-locally.md](how-to/run-locally.md) |
| Understand the system | [architecture.md](architecture.md), [data-model.md](data-model.md) |
| Connect Claude Desktop or Cursor | [how-to/connect-claude-desktop-and-cursor.md](how-to/connect-claude-desktop-and-cursor.md) |
| Look up an endpoint, tool, event, error code or setting | [reference/README.md](reference/README.md) |
| Rebrand the platform (white-label) | [reference/configuration.md](reference/configuration.md#white-labelling) |
| Add a tool, endpoint, migration, provider | [how-to/README.md](how-to/README.md) |
| Debug a tool call or a bad answer | [how-to/debug-a-tool-call.md](how-to/debug-a-tool-call.md), [observability.md](observability.md) |
| Know why a decision was made | [decisions/README.md](decisions/README.md) |
| Deploy everything, or one part alone | [how-to/deploy.md](how-to/deploy.md) |
| Handle an incident | [runbooks/README.md](runbooks/README.md) |
| Security model and test strategy | [security.md](security.md), [testing-strategy.md](testing-strategy.md) |
| See what comes next | [future-improvements.md](future-improvements.md) |

Conventions: every how-to ends with a **Verify** step and a **What usually goes wrong** list;
ADRs are never rewritten (a later ADR amends an earlier one); reference pages are checked against
the code by CI where possible (`scripts/check_tool_docs.py`, the OpenAPI snapshot).
