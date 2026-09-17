from kpi_api.agent.providers.stub import StubLLMProvider, StubTurn, heuristic_turn
from kpi_api.agent.types import TextDelta, ToolUseComplete, TurnEnd


def test_heuristic_first_turn_routes() -> None:
    qtd = heuristic_turn([{"role": "user", "content": "What is ORBY total revenue QTD?"}])
    assert qtd.tool_calls == [
        {"name": "get_kpi_qtd", "input": {"ticker": "ORBY", "kpi": "total_revenue"}}
    ]
    hist = heuristic_turn([{"role": "user", "content": "Show KSTL customers history"}])
    assert (
        hist.tool_calls[0]["name"] == "get_kpi_history"
        and hist.tool_calls[0]["input"]["kpi"] == "paying_customers"
    )
    kpis = heuristic_turn([{"role": "user", "content": "Which KPIs does ORBY publish?"}])
    assert kpis.tool_calls[0]["name"] == "list_company_kpis"
    search = heuristic_turn([{"role": "user", "content": "Tell me about Orbitly Analytics"}])
    assert search.tool_calls[0] == {"name": "search_companies", "input": {"query": "Orbitly"}}
    assert heuristic_turn([{"role": "user", "content": "hello"}]).tool_calls[0]["input"] == {}


def test_heuristic_retries_with_suggestion_then_answers() -> None:
    messages = [
        {"role": "user", "content": "Show ORBYY revenue history"},
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "t1",
                    "name": "get_kpi_history",
                    "input": {"ticker": "ORBYY", "kpi": "total_revenue"},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "t1",
                    "is_error": True,
                    "content": (
                        '{"error":{"code":"company_not_found","suggestions":[{"value":"ORBY"}]}}'
                    ),
                }
            ],
        },
    ]
    retry = heuristic_turn(messages)
    assert retry.tool_calls == [
        {"name": "get_kpi_history", "input": {"ticker": "ORBY", "kpi": "total_revenue"}}
    ]
    messages += [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "t2",
                    "name": "get_kpi_history",
                    "input": {"ticker": "ORBY", "kpi": "total_revenue"},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "t2",
                    "is_error": False,
                    "content": '{"company":{"ticker":"ORBY"},"kpi":{"name":"Total Revenue ($MM)"},'
                    '"count":2,'
                    '"points":[{"period":"2025Q3","value":600,"unit":"$MM"},{"period":"2026Q2","value":627.45,"unit":"$MM"}],"note":null}',
                }
            ],
        },
    ]
    answer = heuristic_turn(messages)
    assert (
        answer.text
        and "2026Q2" in answer.text
        and "627.45 $MM" in answer.text
        and "+4.6%" in answer.text
    )


async def test_scripted_provider_emits_events() -> None:
    provider = StubLLMProvider(
        [StubTurn(text="hi", tool_calls=[{"name": "search_companies", "input": {}}])]
    )
    events = [
        e
        async for e in provider.stream_turn(
            system="s", messages=[{"role": "user", "content": "x"}], tools=[]
        )
    ]
    assert isinstance(events[0], TextDelta)
    assert any(isinstance(e, ToolUseComplete) and e.name == "search_companies" for e in events)
    end = events[-1]
    assert (
        isinstance(end, TurnEnd)
        and end.stop_reason == "tool_use"
        and len(end.assistant_content) == 2
    )
