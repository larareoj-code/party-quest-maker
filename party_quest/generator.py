from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, asdict


MODES = {"scavenger", "escape", "bingo"}
DIFFICULTIES = {"easy", "medium", "hard"}

THEMES = {
    "space": {
        "title": "Space Adventure",
        "story": "A star map has scattered across the celebration. Recover every signal before launch time.",
        "objects": ["something round like a moon", "an object that sparkles", "something with buttons", "a hidden star shape", "something that can fly", "three things in one color"],
        "actions": ["make a five-second robot dance", "pose like an astronaut", "invent a planet name", "count down from ten dramatically"],
    },
    "jungle": {
        "title": "Jungle Expedition",
        "story": "An explorer's field journal is missing. Complete the trail to reveal the final camp.",
        "objects": ["something leaf-shaped", "an animal picture", "something green", "a tiny hiding place", "something that makes a sound", "an object with stripes"],
        "actions": ["move like a sneaky explorer", "make your best bird call", "form a team expedition pose", "cross the room without touching the floor"],
    },
    "celebration": {
        "title": "Confetti Challenge",
        "story": "The party meter needs a boost. Finish the challenges and unlock the grand celebration.",
        "objects": ["something brighter than your shirt", "a party snack", "something shaped like a letter", "an object everyone uses", "something smaller than your hand", "two matching objects"],
        "actions": ["take a team celebration photo", "create a secret handshake", "make someone laugh", "perform a silent birthday cheer"],
    },
    "mystery": {
        "title": "Secret Agent Mystery",
        "story": "A coded message has arrived. Follow the evidence and identify the final password.",
        "objects": ["something with a number", "an object that opens", "something reflected", "a hidden letter", "an object with a pattern", "something that keeps time"],
        "actions": ["whisper a team code name", "walk across the room undercover", "recreate a suspicious pose", "send a message using only gestures"],
    },
}

LOCATIONS = {
    "home": ["entryway", "kitchen", "living room", "bedroom", "hallway", "near a window", "under a table", "by a bookshelf"],
    "outdoors": ["near a tree", "beside a path", "under a bench", "by a fence", "near flowers", "at the starting point", "beside a sign", "in an open space"],
    "office": ["reception", "meeting room", "break area", "near a printer", "by a whiteboard", "at a desk", "near a window", "beside a plant"],
    "anywhere": ["starting area", "near a doorway", "beside a seat", "at a shared table", "near a wall", "in plain sight", "low to the ground", "at the finish area"],
}


@dataclass(frozen=True)
class QuestRequest:
    mode: str
    occasion: str
    age_group: str
    theme: str
    location: str
    players: int
    difficulty: str
    minutes: int
    guest_name: str = ""
    message: str = ""

    @classmethod
    def validate(cls, payload: dict[str, object]) -> "QuestRequest":
        mode = str(payload.get("mode", "scavenger")).lower()
        difficulty = str(payload.get("difficulty", "medium")).lower()
        theme = str(payload.get("theme", "space")).lower()
        location = str(payload.get("location", "home")).lower()
        if mode not in MODES or difficulty not in DIFFICULTIES:
            raise ValueError("Choose a supported game mode and difficulty.")
        if theme not in THEMES or location not in LOCATIONS:
            raise ValueError("Choose a supported theme and location.")
        players = int(payload.get("players", 6))
        minutes = int(payload.get("minutes", 45))
        if not 1 <= players <= 40 or not 15 <= minutes <= 120:
            raise ValueError("Players or game length are outside the supported range.")
        return cls(
            mode=mode,
            occasion=str(payload.get("occasion", "Birthday Party"))[:80],
            age_group=str(payload.get("age_group", "All ages"))[:40],
            theme=theme,
            location=location,
            players=players,
            difficulty=difficulty,
            minutes=minutes,
            guest_name=str(payload.get("guest_name", ""))[:60],
            message=str(payload.get("message", ""))[:180],
        )


def _seed(request: QuestRequest) -> int:
    encoded = "|".join(str(value) for value in asdict(request).values()).encode("utf-8")
    return int(hashlib.sha256(encoded).hexdigest()[:16], 16)


def generate_quest(request: QuestRequest) -> dict[str, object]:
    rng = random.Random(_seed(request))
    theme = THEMES[request.theme]
    count = 8 if request.difficulty == "easy" else 10 if request.difficulty == "medium" else 12
    locations = LOCATIONS[request.location][:]
    rng.shuffle(locations)
    prompts = (theme["objects"] + theme["actions"]) * 2
    rng.shuffle(prompts)
    clues = []
    for index in range(count):
        prompt = prompts[index]
        kind = "challenge" if prompt in theme["actions"] else "find"
        clues.append({
            "number": index + 1,
            "title": f"Mission {index + 1}",
            "prompt": prompt[0].upper() + prompt[1:] + ".",
            "location": locations[index % len(locations)],
            "kind": kind,
            "hint": f"Look {locations[index % len(locations)]}." if kind == "find" else "Commit to the performance as a team.",
            "points": 10 if request.difficulty == "easy" else 15 if request.difficulty == "medium" else 20,
        })
    if request.mode == "escape":
        for index, clue in enumerate(clues):
            clue["prompt"] = f"Solve code {index + 1}: {clue['prompt']} Record the first letter of your answer."
            clue["kind"] = "puzzle"
    if request.mode == "bingo":
        for clue in clues:
            clue["title"] = f"Square {clue['number']}"
            clue["location"] = "anywhere"
    guest = f" for {request.guest_name}" if request.guest_name else ""
    return {
        "id": hashlib.sha1(str(_seed(request)).encode()).hexdigest()[:10],
        "title": f"{theme['title']} {request.mode.replace('_', ' ').title()}",
        "subtitle": f"A {request.occasion.lower()} quest{guest}",
        "story": request.message or theme["story"],
        "mode": request.mode,
        "players": request.players,
        "minutes": request.minutes,
        "difficulty": request.difficulty,
        "clues": clues,
        "pack": ["Welcome page", f"{count} clue cards", "Host guide", "Answer key", "Hint sheet", "Victory certificate"],
        "safety": "Use age-appropriate hiding places. Never require climbing, trespassing, unsafe food, or contact with strangers.",
    }

