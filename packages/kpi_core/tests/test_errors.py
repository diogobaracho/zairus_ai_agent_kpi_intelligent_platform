from kpi_core.errors import CompanyNotFound, KpiError, KpiNotFound, RateLimited, ValidationError
from kpi_core.models import Suggestion


def test_problem_document() -> None:
    err = CompanyNotFound(
        "No company with ticker 'IGX'",
        suggestions=[Suggestion(value="ORBY", label="Orbitly Analytics (ORBY)", score=88.9)],
        recovery_hint="retry",
    )
    problem = err.to_problem(instance="/v1/companies/IGX", trace_id="abc")
    assert problem["status"] == 404 and problem["code"] == "company_not_found"
    assert problem["type"].endswith("#company_not_found")
    assert problem["suggestions"][0]["value"] == "ORBY"
    assert problem["recovery_hint"] == "retry" and problem["trace_id"] == "abc"
    assert problem["instance"] == "/v1/companies/IGX"


def test_tool_envelope_and_extra() -> None:
    err = KpiNotFound("nope", reason="not_published_for_company")
    env = err.to_tool_envelope(trace_id="t1")["error"]
    assert env["code"] == "kpi_not_found" and env["retryable"] is True
    assert env["suggestions"] == [] and env["recovery_hint"] is None
    assert env["reason"] == "not_published_for_company" and env["trace_id"] == "t1"


def test_hierarchy_statuses() -> None:
    assert issubclass(ValidationError, KpiError)
    assert ValidationError("x").status == 400
    assert RateLimited("x").status == 429 and RateLimited("x").retryable
    base = KpiError("boom")
    assert base.to_problem()["title"] == "Internal error" and "trace_id" not in base.to_problem()
