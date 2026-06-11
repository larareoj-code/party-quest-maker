import pytest

from party_quest.generator import QuestRequest, generate_quest


def valid(**updates):
    payload = {"mode": "scavenger", "occasion": "Birthday Party", "age_group": "Kids 8-12", "theme": "space", "location": "home", "players": 6, "difficulty": "medium", "minutes": 45}
    payload.update(updates)
    return QuestRequest.validate(payload)


def test_generation_is_deterministic():
    assert generate_quest(valid()) == generate_quest(valid())


def test_modes_change_pack_content():
    hunt = generate_quest(valid())
    escape = generate_quest(valid(mode="escape"))
    assert hunt["clues"][0]["kind"] != escape["clues"][0]["kind"]


def test_difficulty_controls_length():
    assert len(generate_quest(valid(difficulty="easy"))["clues"]) == 8
    assert len(generate_quest(valid(difficulty="hard"))["clues"]) == 12


def test_unsafe_ranges_are_rejected():
    with pytest.raises(ValueError):
        valid(players=100)


def test_generated_pack_includes_safety_note():
    assert "unsafe" in generate_quest(valid())["safety"].lower()

