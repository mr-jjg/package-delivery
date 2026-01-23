# /tests/test_reporter.py

import pytest
from tools.reporter import Reporter, VerbosityLevel

class TestReporterInit:
    def test_init_accepts_zero_and_positive_values(self):
        Reporter(0)
        Reporter(1)
        Reporter(2)
        Reporter(99)

    def test_init_raises_on_negative_verbosity(self):
        with pytest.raises(ValueError):
            Reporter(-1)

class TestReporterReport:
    def test_report_prints_when_verbosity_meets_level(self, capsys):
        reporter = Reporter(VerbosityLevel.PROG)

        reporter.report(VerbosityLevel.PROG, "hello")
        out = capsys.readouterr().out

        assert out == "hello\n"

    def test_report_prints_when_verbosity_exceeds_level(self, capsys):
        reporter = Reporter(VerbosityLevel.INFO)

        reporter.report(VerbosityLevel.PROG, "progress")
        reporter.report(VerbosityLevel.INFO, "info")

        out = capsys.readouterr().out
        assert out == "progress\ninfo\n"

    def test_report_does_not_print_when_below_level(self, capsys):
        reporter = Reporter(VerbosityLevel.PROG)

        reporter.report(VerbosityLevel.INFO, "should not print")
        out = capsys.readouterr().out

        assert out == ""

    def test_report_handles_none_message(self, capsys):
        reporter = Reporter(VerbosityLevel.INFO)

        reporter.report(VerbosityLevel.INFO, None)
        out = capsys.readouterr().out

        assert out == "None\n"