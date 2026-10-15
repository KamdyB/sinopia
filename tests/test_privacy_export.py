from backend.api.privacy import _csv_safe


def test_csv_export_neutralizes_spreadsheet_formula_prefixes():
    for value in ("=1+1", "+SUM(A1:A2)", "-2+3", "@SUM(A1:A2)", "\tformula", "\rformula"):
        assert _csv_safe(value).startswith("'")
    assert _csv_safe("Athlete 01") == "Athlete 01"
