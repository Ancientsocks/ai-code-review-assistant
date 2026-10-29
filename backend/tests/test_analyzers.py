import subprocess

from app.services import analyzers


def test_ruff_reports_tool_unavailable_when_module_is_missing(monkeypatch):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout="", stderr="No module named ruff")

    monkeypatch.setattr(analyzers.subprocess, "run", fake_run)
    findings = analyzers.run_ruff("print('hello')")

    assert len(findings) == 1
    assert findings[0].source == "system"
    assert findings[0].rule_id == "RUFF_UNAVAILABLE"


def test_bandit_reports_tool_unavailable_when_output_is_invalid(monkeypatch):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout="", stderr="No module named bandit")

    monkeypatch.setattr(analyzers.subprocess, "run", fake_run)
    findings = analyzers.run_bandit("print('hello')")

    assert len(findings) == 1
    assert findings[0].source == "system"
    assert findings[0].rule_id == "BANDIT_UNAVAILABLE"


def test_ruff_parses_findings(monkeypatch):
    output = '[{"code":"F821","message":"Undefined name","location":{"row":3}}]'

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout=output, stderr="")

    monkeypatch.setattr(analyzers.subprocess, "run", fake_run)
    findings = analyzers.run_ruff("print(missing)")

    assert len(findings) == 1
    assert findings[0].rule_id == "F821"
    assert findings[0].line == 3


def test_bandit_parses_findings(monkeypatch):
    output = '{"results":[{"test_id":"B105","test_name":"hardcoded_password_string","issue_severity":"LOW","issue_text":"Possible hardcoded password","line_number":1}]}'

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout=output, stderr="")

    monkeypatch.setattr(analyzers.subprocess, "run", fake_run)
    findings = analyzers.run_bandit("password = 'demo'")

    assert len(findings) == 1
    assert findings[0].rule_id == "B105"
    assert findings[0].line == 1


def test_bandit_uses_a_real_temporary_source_file(monkeypatch):
    def fake_run(command, **kwargs):
        source_path = command[-1]
        with open(source_path, encoding="utf-8") as source:
            assert source.read() == "print('hello')"
        return subprocess.CompletedProcess(
            command,
            0,
            stdout='{"results":[]}',
            stderr="",
        )

    monkeypatch.setattr(analyzers.subprocess, "run", fake_run)
    assert analyzers.run_bandit("print('hello')") == []
