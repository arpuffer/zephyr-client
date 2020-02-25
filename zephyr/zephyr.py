""" ZEPHYR for JIRA Client
    A python client for the Zephyr for Jira plugin from SmartBear.
    Official API documentation is NOT reliable, but can be found here:
    https://getzephyr.docs.apiary.io
"""
import json
from typing import List
from requests import Session
from requests.packages import urllib3
import jira
from .resources import Project, Folder, Execution

_HEADERS = {"Content-Type": "application/json"}
EMPTY_CYCLES_REQUEST = "cycle?expand="

EXECUTIONS_URL = (
    "execution/?projectId={}&versionId={}&cycleId={}&folderId={}"
)
EXECUTIONS_ZQL_URL = "zql/executeSearch?zqlQuery={}"
MOVE_EXEUCTIONS_URL = "cycle/{}/move/executions/folder/{}"

ERROR_DESC = "errorDesc"

urllib3.disable_warnings()


class Zephyr:
    """Client session that leverages a requests.Session to interface with the Zephyr API
    """

    def __init__(
        self,
        server: str,
        basic_auth=None,
        verify: bool = True,
        timeout: int = 10,
    ):
        self.server = server
        self.timeout = timeout
        self.zapi_url = server + "/rest/zapi/latest/"
        self._session = Session()
        self._session.headers.update(_HEADERS)
        self._session.auth = basic_auth
        self._session.verify = verify
        self._projects = None  # assign None for uninitialized state
        self._check_connection()

    @property
    def projects(self):
        """Lazily loaded projects property

        Returns:
            List[Project]:
        """
        if self._projects is None:
            self._load_projects()
        return self._projects

    def _load_projects(self):
        """Loads a list of projects using the jira library.  ZAPI responses are not suitable, as they do not
        contain key names.  See documentation for project loading here:
        https://getzephyr.docs.apiary.io/#reference/utilresource/get-all-projects/get-all-projects
        Response data example is NOT provided, but when calls were made to a real server, project name was not
        present.
        """
        jira_session = jira.JIRA(
            server=self.server, auth=self._session.auth, timeout=self.timeout
        )
        projects = jira_session.projects()
        projects = [Project(name=x.key, id_=x.id, session=self) for x in projects]
        self._projects = projects
        jira_session.close()

    def execution(self, id_):
        return Execution(id_=id_, session=self)

    def project(self, name):
        """Find project by name (also known as key), not by integer id

        Args:
            name (str)

        Returns:
            Project
        """
        try:
            (proj,) = [x for x in self.projects if x.name == name.upper()]
        except ValueError:
            raise jira.JIRAError('Could not find project "%s"' % name)
        return proj

    def executions_zql(self, query: str):
        """Search for executions using ZQL

        Args:
            query (str): ZQL query

        Returns:
            List[Execution]
        """
        url = self.zapi_url + EXECUTIONS_ZQL_URL.format(query)
        response = self.get(url=url)
        response = response.json()
        executions = response.get("executions")
        executions = [Execution(x.get("id"), self) for x in executions]
        return executions

    def get(self, url, params=None, raise_for_error=True):
        response = self._session.get(url=url, params=params, timeout=self.timeout)
        if raise_for_error:
            jira.resilientsession.raise_on_error(response)
            content_error = response.json().get(ERROR_DESC)
            if content_error:
                raise jira.JIRAError(content_error)
        return response

    def put(self, url, data, raise_for_error=True):
        """
        Args:
            url (str)
            data ([type])
            raise_for_error (bool, optional): Defaults to True.

        Raises:
            jira.JIRAError: [description]

        Returns:
            [dict]: response
        """
        response = self._session.put(url=url, data=json.dumps(data), timeout=self.timeout)
        if raise_for_error:
            jira.resilientsession.raise_on_error(response)
            content_error = response.json().get(ERROR_DESC)
            if content_error:
                raise jira.JIRAError(content_error)
        return response

    def move_executions(self, executions: List[Execution], destination_folder: Folder):
        url = self.zapi_url + MOVE_EXEUCTIONS_URL.format(
            destination_folder.cycle, destination_folder.id_
        )
        execution_ids = [x.id_ for x in executions]
        payload = {
            "projectId": destination_folder.project,
            "versionId": destination_folder.version,
            "schedulesList": execution_ids,
        }
        response = self.put(url=url, data=json.dumps(payload))
        if response.status_code != 200:
            raise jira.JIRAError(response=response)

    def _check_connection(self):
        """Verify connection to ZAPI server (called on init)

        Raises:
            ValueError: If server responds, but authentication failed
            ConnectionError: If no parseable response from server
        """
        url = self.zapi_url + EMPTY_CYCLES_REQUEST
        response = self.get(url, raise_for_error=False)
        if (
            response.status_code == 400
        ):  # If authorization is successful and server responds, this request should yield a 400
            return
        jira.resilientsession.raise_on_error(response)

    def _test_spam_calls(self, calls=200):
        failed_responses = []
        project_id = 10204
        version_id = 20418
        cycle_id = 3447
        folder_id = 330
        url = self.zapi_url + EXECUTIONS_URL.format(
            project_id, version_id, cycle_id, folder_id
        )
        for _ in range(calls):
            response = self.get(url)
            if response.status_code != 200:
                failed_responses.append(response.content)
        if failed_responses:
            print("Failed calls: %s" % len(failed_responses))

    def raise_on_error(self, response):
        """If auth=None, the Zephyr API responds with a 200 status and the following content:
            {
             'errorDesc':'You do not have the permission to make this request. Login Required.',
             'errorId': 'ERROR'
            }
        due to this, additional handling has been added to the jira client's raise_on_error method.
        Invalid auth credentials will generate the expected 401 error

        Arguments:
            response {requests.Response}
        """
        if response.status_code == 200 and ERROR_DESC in response.content:
            response.status_code = (
                401  # edit status code on the fly so jira lib method handles it
            )
        jira.resilientsession.raise_on_error(response)
