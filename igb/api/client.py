from typing import List, Optional

import requests
from dataclasses import dataclass, field
from django.conf import settings


@dataclass
class JobBoard:
    name: str
    klass: str
    logo: Optional[str] = None
    moc: Optional[dict] = field(default_factory=dict)
    options: Optional[list] = field(default_factory=list)
    facets: Optional[list] = field(default_factory=list)

    def __str__(self):
        return self.klass

    @property
    def pk(self):
        return self.klass


class IGBJobBoards:
    _instance = None

    def __init__(self, api_key: str, environment_id: str):
        self._api_key = api_key
        self._environment_id = environment_id

    def __new__(cls, api_key: str, environment_id: str):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__(api_key, environment_id)
        return cls._instance

    def list(self) -> Optional[List[JobBoard]]:
        resp = requests.get(
            settings.IGB_URL.format(environment_id=self._environment_id),
            headers={"X-IGB-Api-Key": self._api_key},
        )
        if resp.ok:
            job_boards = resp.json()["HAPI"]["jobboards"]
            return [
                JobBoard(
                    name=job_board["jobboard"]["name"],
                    klass=job_board["jobboard"]["class"],
                    logo=job_board["jobboard"]["logo"],
                )
                for job_board in job_boards
            ]

    def detail(self, job_board: str) -> Optional[JobBoard]:
        resp = requests.get(
            settings.IGB_URL.format(environment_id=self._environment_id)
            + f"/{job_board}",
            headers={"X-IGB-Api-Key": self._api_key},
        )
        if resp.ok:
            job_board = resp.json()["HAPI"]["jobboard"]
            if job_board:
                return JobBoard(
                    name=job_board["name"],
                    klass=job_board["class"],
                    moc=job_board["MOC"],
                    facets=job_board["facets"],
                )


def get_singleton_client() -> IGBJobBoards:
    return IGBJobBoards(settings.IGB_API_KEY, settings.IGB_API_ENVIRONMENT_ID)
