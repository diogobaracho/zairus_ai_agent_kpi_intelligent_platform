"""Pure mapping helpers of the Anthropic provider (the network path is exercised by `-m live`)."""

from types import SimpleNamespace

from kpi_api.agent.providers.anthropic_provider import content_to_dicts, map_stop_reason


class _Block:
    def __init__(self, **fields: object) -> None:
        self._fields = fields

    def model_dump(self, exclude_none: bool = False) -> dict[str, object]:
        return {k: v for k, v in self._fields.items() if not (exclude_none and v is None)}


def test_mapping_helpers() -> None:
    assert map_stop_reason("tool_use") == "tool_use" and map_stop_reason(None) == "end_turn"
    assert map_stop_reason("weird") == "end_turn"
    blocks = [
        _Block(type="text", text="hi", citations=None),
        _Block(type="thinking", thinking="", signature="sig"),
    ]
    assert content_to_dicts(blocks) == [
        {"type": "text", "text": "hi"},
        {"type": "thinking", "thinking": "", "signature": "sig"},
    ]
    assert SimpleNamespace  # keep import used
