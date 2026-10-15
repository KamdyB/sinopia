from sqlalchemy import inspect, text
from backend.data.db import create_tables, make_engine


def test_existing_player_table_is_upgraded_to_team_scope(tmp_path):
    engine = make_engine("sqlite:///" + str(tmp_path / "legacy.db"))
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE players (player_id TEXT PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE, "
            "team_type TEXT NOT NULL, registered_date TEXT NOT NULL)"
        ))
        connection.execute(text(
            "CREATE UNIQUE INDEX idx_players_team_name ON players (team_type, name)"
        ))
        connection.execute(text(
            "INSERT INTO players (player_id, name, team_type, registered_date) "
            "VALUES ('old-id', 'Athlete', 'girls', '2026-01-01')"
        ))

    create_tables(engine)
    with engine.connect() as connection:
        row = connection.execute(text("SELECT team_id FROM players WHERE player_id='old-id'")).one()
    assert row[0] == "legacy-girls"
    assert "team_id" in {column["name"] for column in inspect(engine).get_columns("players")}
    assert "idx_players_team_name" not in {index["name"] for index in inspect(engine).get_indexes("players")}
