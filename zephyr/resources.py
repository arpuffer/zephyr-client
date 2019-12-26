import logging
from requests import Session, HTTPError
from config import SERVER

logger = logging.getLogger(__name__)

JIRA_URL = SERVER + '/rest/api/2/'
ZAPI_URL = SERVER + '/rest/zapi/latest/'

PROJECT_URL = JIRA_URL + 'project'
EXECUTION_URL = ZAPI_URL + 'execution'
GETEXECUTIONS_URL = EXECUTION_URL + '?projectId={}&versionId={}&folderId={}&cycleId={}'
CYCLE_URL = ZAPI_URL + 'cycle'
GETCYCLES_URL = CYCLE_URL + '?projectId={}&versionId={}'  # unsure why ampersand not required after '?' here
FOLDERS_URL = ZAPI_URL + 'cycle/{}/folders?projectId={}&versionId={}&limit=&offset='
STEPS_URL = ZAPI_URL + 'stepResult?executionId={}'


class Resource():
    def __init__(self,
                 name: str,
                 id: int,
                 session = None):
        self.name = name
        self.id = id
        self._session: Session = session
        self.url = None
        self._raw = None
    
    @property
    def raw(self):
        if not self._raw:
            self._load()
        return self._raw

    def _load(self):
        self._raw = self._session.get(self.url, timeout=self._session.timeout)

class Project(Resource):
    # TODO: Pull in from the jira lib(?)
    def __init__(self, name, id, session):
        super().__init__(name, id, session)
        self.url = PROJECT_URL + '/{}'.format(id)
        self._versions = None

    @property
    def versions(self):
        if self._versions == None:
            self._load_versions()
        return self._versions

    def version(self, version_name):
        version, = [x for x in self.versions if x.name == version_name]
        return version

    def _load_versions(self):
        response = self._session.get(self.url, timeout=self._session.timeout)
        response = response.json()
        raw_versions = response['versions']
        versions = [Version(name = x['name'],
                            id = x['id'],
                            project = self.id,
                            session = self._session) for x in raw_versions]
        self._versions = versions

class Test(Resource):
    def __init__(self):
        raise NotImplementedError

class Version(Resource):
    # Child of Project
    # TODO: Pull in from the jira lib(?)
    def __init__(self, name, id, session, project):
        super().__init__(name, id, session)
        self.project = project
        self._cycles = None

    @property
    def cycles(self):
        if self._cycles == None:
            self._load_cycles()
        return self._cycles

    def _load_cycles(self):
        cycles = []
        url = GETCYCLES_URL.format(self.project, self.id)
        response = self._session.get(url, timeout=self._session.timeout)
        cycles_dict = response.json()  # dict in this casee
        cycles_dict.pop('recordsCount')
        for k,v in cycles_dict.items():
            cycle = Cycle(name=v['name'],
                          id=k,
                          session=self._session,
                          version = self.id,
                          project = self.project)
            cycles.append(cycle)
        self._cycles = cycles

class Cycle(Resource):
    # Child of Version (aka fixVersion)
    def __init__(self, name, id, session, version, project):
        super().__init__(name, id, session)
        self.project = project
        self.version = version
        self.url = CYCLE_URL + '/{}/'.format(id)
        self._folders = None

    @property
    def folders(self):
        if self._folders == None:
            self._load_folders()
        return self._folders

    def _load_folders(self):
        url = self.url + 'folders?'
        params = {'projectId': self.project,
                    'versionId': self.version}
        folders = self._session.get(url, params=params, timeout=self._session.timeout)
        folders = folders.json()  # returns a list in this case -- there is not much consistency in Zephyr
        self._folders = [Folder(name=x['folderName'],
                                id=x['folderId'],
                                project=self.project,
                                version=self.version,
                                cycle=self.id,
                                session=self._session) for x in folders]

class Folder(Resource):
    """
    Child of Cycle, NOT a resource entity.  Used only to query for executions.
    Execution querying requires a folder, and cannot be done from higher levels except via ZQL.
    All that exists for folder is a name and an ID integer
    """
    def __init__(self, name, id, project, version, cycle, session):
        super().__init__(name, id, session)
        self.project = project
        self.version = version
        self.cycle = cycle
        self._executions = None

    @property
    def executions(self):
        if self._executions == None:
            self._load_executions()
        return self._executions

    def _load_executions(self):
        url = GETEXECUTIONS_URL.format(self.project, self.version, self.id, self.cycle)
        executions = self._session.get(url, timeout=self._session.timeout)
        executions = executions.json()  # list in this case
        executions = executions['executions']
        self._executions = [Execution(id=x['id'],
                                      session=self._session) for x in executions]

class Execution(Resource):
    def __init__(self, id, session):
        super().__init__(name=None, id=id, session=session)
        self.url = EXECUTION_URL + '/{}'.format(id)
        self._raw = None
        self._steps = None

    @property
    def raw(self):
        if self._raw == None:
            self._load()
        return self._raw

    @property
    def steps(self):
        if self._steps == None:
            self._load_steps()
        return self._steps
    
    def _load(self):
        raw = self._session.get(self.url, timeout=self._session.timeout)
        self._raw = raw.json()

    def _load_steps(self):
        # TODO: See links in slack from Aaron, latest changes in master
        url = STEPS_URL.format(self.id)
        steps = self._session.get(url, timeout=self._session.timeout)
        steps = steps.json()  # list in this case
        self._steps = steps # maybe parse into an object later, maybe stop caring while I'm ahead

    def assign(self, user: str):
        url = self.url + '?assignee={}'.format(user)
        response = self._session.post(url, timeout=self._session.timeout)
        if response.code != 200:
            raise HTTPError('Assign failed, code: %s', response.code)
        logger.debug('Assigned execution %s to %s', self.id, user)


    def move(self, folder: Resource):
        """ REFERENCE FROM OLD IMPLEMENTATION
        def move_executions(project, fixVersion, cycle, folder, executions):
            url = "https://jira.MYSERVER.net/rest/zapi/latest/cycle/%s/move/executions/folder/%s"
            url = url % (cycle.id, folder.id)
            execution_ids = [x.id for x in executions]
            payload = '{"projectId": %s, "versionId": %s, "schedulesList": %s}' % (project.id, fixVersion.id, execution_ids)
            response = requests.request("PUT", url, data=payload, headers=headers, auth=(user, passwd))
            if js_res.status_code != 200:
                print(js_res)
                raise Exception('### Error, bad server response %s ###' % js_res.status_code)
            return executions
        """
        raise NotImplementedError

    def update(self, status=None, comment=None):
        raise NotImplementedError