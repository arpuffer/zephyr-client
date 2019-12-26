''' ZEPHYR for JIRA Client
    A python client for the Zephyr for Jira plugin from SmartBear.
    Official API documentation is NOT reliable, but can be found here:
    https://getzephyr.docs.apiary.io
'''
from typing import List
from requests import Session
import jira
from resources import Project
from config import (SERVER,
                    USER,
                    PASSWORD,
                    VERIFY,
                    TIMEOUT)

HEADERS = {"Content-Type": "application/json"}
JIRA_URL = SERVER + '/rest/api/2/'
ZAPI_URL = SERVER + '/rest/zapi/latest/'

EXECUTIONS_URL = ZAPI_URL + 'execution/?projectId={}&versionId={}&cycleId={}&folderId={}'
EXECUTIONS_URL = ZAPI_URL + 'execution?projectId={}&versionId={}&cycleId={}&folderId={}'
EXECUTIONS_ZQL_URL = ZAPI_URL + 'zql/executeSearch?zqlQuery={}'
STEPS_URL = ZAPI_URL + 'stepResult?executionId={}'

class Zephyr():
    """Client session that leverages a requests.Session to interface with the Zephyr API
    """
    def __init__(self,
                 server=SERVER,
                 basic_auth=None,
                 headers=HEADERS,
                 verify: bool = VERIFY,
                 timeout: int = TIMEOUT):
        self.server: str = server
        self._session = Session()
        self._session.timeout = timeout
        self._session.headers.update(headers)
        if basic_auth:
            self._session.auth = basic_auth
        else:
            self._session.auth = (USER, PASSWORD)
        self.timeout = timeout
        self._session.verify = verify
        self._projects = None  # assign None for uninitialized state

    @property
    def projects(self) -> List[Project]:
        """Lazily loaded projects property

        Returns:
            List[Project]:
        """
        if self._projects is None:
            self._load_projects()
        return self._projects

    def _load_projects(self):
        jira_session = jira.JIRA(server=self.server, auth=self._session.auth, timeout=20)
        projects = jira_session.projects()
        projects = [Project(name=x.key,
                            id_=x.id,
                            session=self._session) for x in projects]
        self._projects = projects
        jira_session.close()

    def project(self, name):
        """Find project by name (also known as key), not by integer id

        Args:
            name (str)

        Returns:
            Project
        """
        proj, = [x for x in self.projects if x.name == name]
        return proj

    def executions_zql(self, query: str):
        """Search for executions using ZQL

        Args:
            query (str): ZQL query

        Returns:
            List[Execution]
        """
        url = EXECUTIONS_ZQL_URL.format(query)
        response = self._session.get(url, timeout=self._session.timeout)
        return response.json()
