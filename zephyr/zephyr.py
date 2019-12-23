from requests import Request, Session
from typing import List, Tuple, Union, NamedTuple
from .config import (SERVER,
                    USER,
                    PASSWORD,
                    VERIFY)
HEADERS = {"Content-Type": "application/json"}
ZAPI_URL = SERVER + '/rest/zapi/latest/'
CYCLES_URL = ZAPI_URL + 'cycle/?projectId={}&versionId={}'
EXECUTIONS_URL = ZAPI_URL + 'execution/?projectId={}&versionId={}&cycleId={}&folderId={}'

class Resource(NamedTuple):
    name: str
    id: int

class Zephyr():
    def __init__(self,
                 server = SERVER,
                 basic_auth = None,
                 headers = None,
                 verify: bool = VERIFY):
        self.server = server
        self._session = Session()
        self._session.headers.update(headers)
        if basic_auth:
            self._session.auth = basic_auth
        else:
            self._session.auth = (USER, PASSWORD)
        self._session.verify = verify
        

    def cycles(self,
               project: Union[int, str, Resource],
               version: Union[int, str, Resource]) -> List[Resource]:

        # If integer, it's a project/version ID.  Else, assume it is the project/version name.
        # https://community.atlassian.com/t5/Jira-questions/project-key-starting-with-numbers/qaq-p/128566
        pass

    def folders(self,
                project: Union[int, Resource],
                version: Union[int, Resource],
                cycle: Union[int, Resource]) -> List[Resource]:
        pass

    def executions(self,
                   project,
                   version,
                   cycle,
                   folder,
                   zql=None) -> List[Resource]:
        pass

    def update_execution(self,
                         execution: Resource,
                         status: int,
                         comment: str):
        pass