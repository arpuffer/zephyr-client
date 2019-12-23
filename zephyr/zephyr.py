from typing import (List,
                    Optional,
                    Tuple,
                    Union,
                    NamedTuple)
from requests import Request, Session
import jira

from config import (SERVER,
                    USER,
                    PASSWORD,
                    VERIFY,
                    TIMEOUT)
HEADERS = {"Content-Type": "application/json"}
ZAPI_URL = SERVER + '/rest/zapi/latest/'
CYCLES_URL = ZAPI_URL + 'cycle/?projectId={}&versionId={}'
EXECUTIONS_URL = ZAPI_URL + 'execution/?projectId={}&versionId={}&cycleId={}&folderId={}'

class Resource():
    def __init__(self,
                 name: Union[str, int],
                 id: int,
                 description: str,
                 url: str,
                 parent = None,
                 children = []):
        self.name = name
        self.id = id
        self.description = description
        self.url = url
        self.parent = parent
        self._children = children

class ExecutionResource(Resource):
    def __init__(self, parent_folder: Resource):
        super().__init__(parent_folder)
        pass

    def assign(self, user: str):
        pass

    def move(self, folder: Resource):
        pass

    def update(self, status=None, comment=None):
        pass


class Zephyr():
    def __init__(self,
                 server = SERVER,
                 basic_auth = None,
                 headers = HEADERS,
                 verify: bool = VERIFY,
                 timeout: int = TIMEOUT):
        self.server: str = server
        self._session = Session()
        self._session.headers.update(headers)
        if basic_auth:
            self._session.auth = basic_auth
        else:
            self._session.auth = (USER, PASSWORD)
        self.timeout = timeout
        self._session.verify = verify
        self._projects: list = []  # Lazy loaded list

    @property
    def projects(self) -> List[Resource]:
        if not self._projects:
            jira_session = jira.JIRA(server=self.server, auth=self._session.auth, timeout=20)
            projects = jira_session.projects()
            projects = [Resource(x.key, x.id, x.name, x.self) for x in projects]
            self._projects = projects
            jira_session.close()
        return self._projects

    def cycles(self,
               project: Union[int, str, Resource],
               version: Union[str, Resource]) -> dict:
        """Get cycles for given jira fix version
        
        Args:
            project (Union[int, str, Resource]): project (int assumes id, str assumes name, Resource contains both)
            version (Union[str, Resource]): Fix Version (child of project, str assumes name, Resource contains name and id)
        
        Raises:
            TypeError: if project not int, str, or Resource
            TypeError: if version not str or Resource
        
        Returns:
            dict: json response  # TODO: Return List[Resource]
        """
        if isinstance(project, str):
            project_id, = [x.id for x in self.projects if x.name == project]  # Trailing comma raises ValueError if len(list) > 1, and we only expect one match 
        elif isinstance(project, Resource):
            project_id = project.id
        elif isinstance(project, int):
            project_id = project
        else:
            raise TypeError('project must be int or Resource')
        if isinstance(version, str):
            jira_session = jira.JIRA(server=self.server, auth=self._session.auth, timeout=20)
            jira_project = jira_session.project(project_id)
            versions = jira_project.versions()
            version_id, = [x.id for x in versions if x.name == version]
        elif isinstance(version, Resource):
            version_id = version.id
        else:
            raise TypeError('version must be str or Resource')
        url = CYCLES_URL.format(project_id, version_id)
        response = self._session.get(url, timeout=self.timeout)
        # If integer, it's a project/version ID.  Else, assume it is the project/version name.
        # https://community.atlassian.com/t5/Jira-questions/project-key-starting-with-numbers/qaq-p/128566
        return response.json()

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
