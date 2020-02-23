""" Zephyr Client Resource objects and accompanying methods """
import logging


logger = logging.getLogger(__name__)

JIRA_URL = "{}/rest/api/2/"
ZAPI_URL = "{}/rest/zapi/latest/"

PROJECT_URL = JIRA_URL + "project"
EXECUTION_URL = ZAPI_URL + "execution"
GETEXECUTIONS_URL = EXECUTION_URL + "?projectId={}&versionId={}&folderId={}&cycleId={}"
CYCLE_URL = ZAPI_URL + "cycle"
GETCYCLES_URL = CYCLE_URL + "?projectId={}&versionId={}"
FOLDERS_URL = ZAPI_URL + "cycle/{}/folders?projectId={}&versionId={}&limit=&offset="
STEPS_URL = ZAPI_URL + "stepResult?executionId={}"


class Resource:
    """Base class for Jira/Zephyr Resources"""

    def __init__(self, name: str, id_: int, session):
        self.name = name
        self.id_ = id_
        self.zephyr_session = session


class Project(Resource):
    """Jira Project Resource.  This is the top-level resource.
    Use the jira library for advanced operations
    """

    # TODO: Pull in from the jira lib(?)
    def __init__(self, name, id_, session):
        super().__init__(name, id_, session)
        self.url = PROJECT_URL.format(self.zephyr_session.server) + "/{}".format(id_)
        self._versions = None

    @property
    def versions(self):
        if self._versions is None:
            self._load_versions()
        return self._versions

    def version(self, version_name):
        """Find version (also known as fixVersion) by name

        Args:
            version_name (str)

        Returns:
            Version
        """
        (version,) = [x for x in self.versions if x.name == version_name]
        return version

    def _load_versions(self):
        response = self.zephyr_session.get(self.url)
        response = response.json()
        raw_versions = response["versions"]
        versions = [
            Version(
                name=x["name"],
                id_=x["id"],
                project=self.id_,
                session=self.zephyr_session,
            )
            for x in raw_versions
        ]
        self._versions = versions


class Test(Resource):
    """ Zephyr Test Resource """

    def __init__(self, name, id_, session, project):
        super().__init__(name, id_, session)
        raise NotImplementedError


class Version(Resource):
    """ Jira Version (fixVersion) resource.  For more advanced tools,
    use the jira library.  Child of Project resource.
    TODO: Pull in from the jira lib(?)
    """

    def __init__(self, name, id_, session, project):
        super().__init__(name, id_, session)
        self.project = project
        self._cycles = None

    @property
    def cycles(self):
        if self._cycles is None:
            self._load_cycles()
        return self._cycles

    def cycle(self, cycle_name):
        (match,) = [x for x in self.cycles if x.name == cycle_name]
        return match

    def _load_cycles(self):
        cycles = []
        url = GETCYCLES_URL.format(self.zephyr_session.server, self.project, self.id_)
        response = self.zephyr_session.get(url)
        cycles_dict = response.json()  # dict in this casee
        cycles_dict.pop("recordsCount")
        for k, v in cycles_dict.items():
            cycle = Cycle(
                name=v["name"],
                id_=k,
                session=self.zephyr_session,
                version=self.id_,
                project=self.project,
            )
            cycles.append(cycle)
        self._cycles = cycles


class Cycle(Resource):
    """ Zephyr Test Cycle resource, child of Version (fixVersion) """

    def __init__(self, name, id_, session, version, project):
        super().__init__(name, id_, session)
        self.project = project
        self.version = version
        self.url = CYCLE_URL.format(self.zephyr_session.server) + "/{}/".format(id_)
        self._folders = None

    @property
    def folders(self):
        if self._folders is None:
            self._load_folders()
        return self._folders

    def folder(self, folder_name):
        (matched_folder,) = [x for x in self.folders if x.name == folder_name]
        return matched_folder

    def _load_folders(self):
        url = self.url + "folders?"
        params = {"projectId": self.project, "versionId": self.version}
        folders = self.zephyr_session.get(url, params=params)
        folders = (
            folders.json()
        )  # returns a list in this case -- not much consistency in Zephyr
        self._folders = [
            Folder(
                name=x["folderName"],
                id_=x["folderId"],
                project=self.project,
                version=self.version,
                cycle=self.id_,
                session=self.zephyr_session,
            )
            for x in folders
        ]


class Folder(Resource):
    """ Zephyr Folder resource
    Child of Cycle, NOT an actual resource entity.  Used only to query for executions.
    Execution querying requires a folder, and cannot be done from higher levels except via ZQL.
    All that exists for folder is a name and an ID integer
    """

    def __init__(self, name, id_, project, version, cycle, session):
        super().__init__(name, id_, session)
        self.project = project
        self.version = version
        self.cycle = cycle
        self._executions = None

    @property
    def executions(self):
        if self._executions is None:
            self._load_executions()
        return self._executions

    def _load_executions(self):
        url = GETEXECUTIONS_URL.format(self.project, self.version, self.id_, self.cycle)
        executions = self.zephyr_session.get(url)
        executions = executions.json()  # list in this case
        executions = executions["executions"]
        self._executions = [
            Execution(id_=x["id"], session=self.zephyr_session) for x in executions
        ]


class Execution(Resource):
    """ Zephyr Test Execution resource.  This resource is a distinct execution of a test
    for a given Folder
    """

    def __init__(self, id_, session):
        super().__init__(name=None, id_=id_, session=session)
        self.session = session
        self.url = session.zapi_url + "execution/" + str(id_)
        self._raw = None
        self._steps = None

    @property
    def raw(self):
        if self._raw is None:
            self._load()
        return self._raw

    @property
    def steps(self):
        if self._steps is None:
            self._load_steps()
        return self._steps

    @property
    def assignee(self):
        return self.raw.get("assignee")

    def comment(self):
        return self.raw.get("comment")

    @property
    def folder_id(self):
        return self.raw.get("folderId")

    @property
    def status(self):
        return self.raw.get("executionStatus")

    def _load(self):
        raw = self.zephyr_session.get(self.url)
        self._raw = raw.json()

    def _load_steps(self):
        # TODO: See links in slack from Aaron, latest changes in master
        url = STEPS_URL.format(self.id_)
        steps = self.zephyr_session.get(url)
        steps = steps.json()  # list in this case
        self._steps = (
            steps  # maybe parse into an object later, maybe stop caring while I'm ahead
        )

    def assign(self, user: str):
        """Assign execution to user
        Args:
            user (str): id, not name (john.smith, not John Smith)

        Raises:
            HTTPError: on failure to assign
        """
        payload = {
            "assignee": user,
            "assigneeType": "assignee",
            "changeAssignee": True
        }
        response = self.execute(payload=payload)
        logger.debug("Assigned execution %s to %s", self.id_, user)
        return response

    def unassign(self):
        payload = {
            "changeAssignee": True
        }
        return self.execute(payload=payload)

    def execute(self, payload):
        url = self.url + "/execute"
        return self.zephyr_session.put(url, data=payload)

    def update(self, status=None, comment=None):
        raise NotImplementedError
