import pytest

from shiftlog.cli import main


def test_summary_smoke(capsys):
    assert main(["examples/tiny.txt"]) == 0
    out = capsys.readouterr().out
    assert "alpha" in out and "beta" in out
    assert out.strip().splitlines()[-1].startswith("TOTAL")


def test_missing_file(capsys):
    assert main(["examples/does-not-exist.txt"]) == 2
    assert "no such file" in capsys.readouterr().err


def test_bad_line_is_reported(tmp_path, capsys):
    path = tmp_path / "bad.txt"
    path.write_text("2026-01-05 1h alpha\nrubbish\n", encoding="utf-8")
    assert main([str(path)]) == 1
    assert "line 2" in capsys.readouterr().err


@pytest.mark.parametrize("flag", ["--csv"])
def test_alternate_views_run(flag, capsys):
    assert main([flag, "examples/tiny.txt"]) == 0
    assert capsys.readouterr().out.strip()
