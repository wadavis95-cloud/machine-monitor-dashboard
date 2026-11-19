from html.parser import HTMLParser

import pytest

from app import create_app


class ElementIdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        self.ids.update(value for name, value in attrs if name == "id")


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_next_returns_http_200(client):
    response = client.get("/api/engine/1/next")
    assert response.status_code == 200


def test_next_returns_engine_fields_as_json(client):
    response = client.get("/api/engine/1/next")
    expected = {"unit", "cycle"} | {f"s_{number}" for number in range(1, 22)}
    assert response.is_json
    row = response.get_json()
    assert expected <= row.keys()
    assert row["unit"] == 1


def test_each_engine_advances_one_cycle_independently(client):
    first_1 = client.get("/api/engine/1/next").get_json()
    first_2 = client.get("/api/engine/2/next").get_json()
    second_1 = client.get("/api/engine/1/next").get_json()
    second_2 = client.get("/api/engine/2/next").get_json()

    assert first_1["cycle"] == first_2["cycle"] == 1
    assert second_1["cycle"] == first_1["cycle"] + 1
    assert second_2["cycle"] == first_2["cycle"] + 1


def test_next_returns_done_after_the_final_cycle(client):
    for cycle in range(1, 193):
        response = client.get("/api/engine/1/next")
        assert response.get_json()["cycle"] == cycle

    response = client.get("/api/engine/1/next")
    assert response.get_json() == {"done": True}


def test_dashboard_returns_http_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_dashboard_has_required_element_ids(client):
    response = client.get("/")
    parser = ElementIdParser()
    parser.feed(response.get_data(as_text=True))
    assert {"cycle", "s_2", "s_3", "s_4", "chart"} <= parser.ids
