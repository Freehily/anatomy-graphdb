from typing import Optional, Sequence, Tuple

from fastapi.testclient import TestClient

from stronger.api.main import ExerciseRecord, ExerciseRepository, create_app


class StubExerciseRepository(ExerciseRepository):
    def __init__(self) -> None:
        self.records = [
            ExerciseRecord(
                id="ab_wheel_kneeling_rollout",
                name="Ab Wheel Kneeling Rollout",
                body_region="core",
                level="beginner",
                target_muscle_group="abdominals",
                data={"name": "Ab Wheel Kneeling Rollout"},
            ),
            ExerciseRecord(
                id="ab_wheel_standing_rollout",
                name="Ab Wheel Standing Rollout",
                body_region="core",
                level="advanced",
                target_muscle_group="abdominals",
                data={"name": "Ab Wheel Standing Rollout"},
            ),
            ExerciseRecord(
                id="push_press",
                name="Push Press",
                body_region="upper_body",
                level="intermediate",
                target_muscle_group="shoulders",
                data={"name": "Push Press"},
            ),
        ]

    def list_exercises(
        self,
        *,
        search: Optional[str],
        body_region: Optional[str],
        template: Optional[str],
        limit: int,
        offset: int,
    ) -> Tuple[int, Sequence[ExerciseRecord]]:
        filtered = self.records
        if search:
            lower = search.lower()
            filtered = [record for record in filtered if lower in record.name.lower()]
        if body_region:
            filtered = [record for record in filtered if record.body_region == body_region]
        total = len(filtered)
        window = filtered[offset : offset + limit]
        return total, window

    def get_exercise(self, exercise_id: str) -> ExerciseRecord:
        for record in self.records:
            if record.id == exercise_id:
                return record
        raise KeyError(exercise_id)


client = TestClient(create_app(repository=StubExerciseRepository()))


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_exercises_defaults() -> None:
    response = client.get("/exercises")
    assert response.status_code == 200
    payload = response.json()
    assert payload["limit"] == 50
    assert payload["offset"] == 0
    assert payload["total"] >= len(payload["items"])
    assert payload["items"], "Expected at least one exercise to be returned"


def test_filter_by_body_region() -> None:
    response = client.get("/exercises", params={"body_region": "core", "limit": 5})
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"]
    assert all(item["body_region"] == "core" for item in payload["items"])


def test_get_exercise_by_id() -> None:
    response = client.get("/exercises/ab_wheel_kneeling_rollout")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ab_wheel_kneeling_rollout"
    assert data["data"]["name"] == "Ab Wheel Kneeling Rollout"


def test_search_is_case_insensitive() -> None:
    response = client.get("/exercises", params={"search": "standing rollout"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert any(item["id"] == "ab_wheel_standing_rollout" for item in items)


def test_missing_exercise_returns_404() -> None:
    response = client.get("/exercises/not-real")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
