from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto


@dataclass
class SummonerInfo:
    puuid: str
    summoner_id: str
    name: str
    # solo rank information
    tier: str = ""
    division: str = ""
    tier_group: TierGroup = field(init=False)
    lp: int = 0
    win: int = 0
    lose: int = 0
    written_timestamp: float = 0  # unix timestamp

    def __post_init__(self):
        self.tier_group = TierGroup.get_from_rank(self.tier, self.division)

    @classmethod
    # get from a save file
    def from_dict(self, dict_data: dict) -> SummonerInfo:
        return SummonerInfo(
            puuid=dict_data.get("puuid"),
            summoner_id=dict_data.get("summoner_id"),
            name=dict_data.get("name"),
            tier=dict_data.get("tier"),
            division=dict_data.get("division"),
            lp=dict_data.get("lp"),
            win=dict_data.get("win"),
            lose=dict_data.get("lose"),
            written_timestamp=dict_data.get("written_time"),
        )

    def to_dict(self) -> dict:
        return {
            "puuid": self.puuid,
            "summoner_id": self.summoner_id,
            "name": self.name,
            "tier": self.tier,
            "division": self.division,
            "lp": self.lp,
            "win": self.win,
            "lose": self.lose,
            "written_time": self.written_timestamp,
        }

    def to_meta_dict(self) -> dict:
        return {
            "tier": self.tier,
            "rank": self.division,
            "lp": self.lp,
            "wins": self.win,
            "losses": self.lose,
            "updated": self.written_timestamp,
        }

    @property
    def rank_number(self) -> int:
        return rank_to_number(self.tier, self.division)


def rank_to_number(tier: str, division: str) -> int:
    index = 0
    if division == "II":
        index = -1
    elif division == "III":
        index = -2
    elif division == "IV":
        index = -3

    if tier == "IRON":
        index += 4 * 1
    elif tier == "BRONZE":
        index += 4 * 2
    elif tier == "SILVER":
        index += 4 * 3
    elif tier == "GOLD":
        index += 4 * 4
    elif tier == "PLATINUM":
        index += 4 * 5
    elif tier == "DIAMOND":
        index += 4 * 6
    elif tier == "MASTER":
        index += 4 * 6 + 1
    elif tier == "GRANDMASTER":
        index += 4 * 6 + 2
    elif tier == "CHALLENGER":
        index += 4 * 6 + 3
    return index


@dataclass
class MatchInfo:
    game_id: int
    version: str
    creation: int
    duration: int
    end_time: int
    participants: list[dict]

    @property
    def participants_puuid(self) -> list:
        return [p["puuid"] for p in self.participants]


class TierGroup(Enum):
    I34 = auto()  # Iron 4 ~ 3
    I12 = auto()  # Iron 2 ~ 1
    B34 = auto()  # Bronze 4 ~ 3
    B12 = auto()  # Broneze 2 ~ 1
    S34 = auto()  # Silver 4 ~ 3
    S12 = auto()  # Silver 2 ~ 1
    G34 = auto()  # Gold 4 ~ 3
    G12 = auto()  # Gold 2 ~ 1
    P34 = auto()  # Platinum 4 ~ 3
    P12 = auto()  # Platinum 2 ~ 1
    D34 = auto()  # Diamond 4 ~ 3
    D12 = auto()  # Diamond 2 ~ 1
    M1 = auto()  # Master
    GM1 = auto()  # Grandmaster
    C1 = auto()  # Challenger
    A = auto()  # Apex = Challenger + Grandmaster
    U = auto()  # Unranked

    @classmethod
    def get_from_rank(cls, tier: str, division: str) -> TierGroup:
        return cls.get_from_rank_number(rank_to_number(tier, division))

    @classmethod
    def get_from_rank_number(cls, rank_number: int) -> TierGroup:
        if rank_number <= 0:
            return cls.U
        elif rank_number <= 2:
            return cls.I34
        elif rank_number <= 4:
            return cls.I12
        elif rank_number <= 6:
            return cls.B34
        elif rank_number <= 8:
            return cls.B12
        elif rank_number <= 10:
            return cls.S34
        elif rank_number <= 12:
            return cls.S12
        elif rank_number <= 14:
            return cls.G34
        elif rank_number <= 16:
            return cls.G12
        elif rank_number <= 18:
            return cls.P34
        elif rank_number <= 20:
            return cls.P12
        elif rank_number <= 22:
            return cls.D34
        elif rank_number <= 24:
            return cls.D12
        elif rank_number == 25:
            return cls.M1
        elif rank_number == 26:
            return cls.GM1
        elif rank_number == 27:
            return cls.C1
        return cls.U

    def is_adjacent_rank(self, rank_number: int) -> bool:
        if self == TierGroup.I34:
            return rank_number in range(1, 4)
        elif self == TierGroup.I12:
            return rank_number in range(2, 6)
        elif self == TierGroup.B34:
            return rank_number in range(4, 8)
        elif self == TierGroup.B12:
            return rank_number in range(6, 10)
        elif self == TierGroup.S34:
            return rank_number in range(8, 12)
        elif self == TierGroup.S12:
            return rank_number in range(10, 14)
        elif self == TierGroup.G34:
            return rank_number in range(12, 16)
        elif self == TierGroup.G12:
            return rank_number in range(14, 18)
        elif self == TierGroup.P34:
            return rank_number in range(16, 20)
        elif self == TierGroup.P12:
            return rank_number in range(18, 22)
        elif self == TierGroup.D34:
            return rank_number in range(20, 24)
        elif self == TierGroup.D12:
            return rank_number in range(22, 26)
        elif self == TierGroup.M1:
            return rank_number in range(24, 28)
        elif self == TierGroup.GM1:
            return rank_number in range(25, 28)
        elif self == TierGroup.C1:
            return rank_number in range(25, 28)
