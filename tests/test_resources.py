import unittest
from .test_client import ZephyrTestCase
from zephyr import execution_status
from zephyr.resources import (Resource,
                              Project,
                              Version,
                              Cycle,
                              Folder,
                              Execution)

VALID_VERSION_NAME = 'validVersion'
INVALID_VERSION_NAME = 'invalidVersion'
VALID_CYCLE_NAME = 'validCycle'
INVALID_CYCLE_NAME = 'invalidCycle'
VALID_FOLDER_NAME = 'validFolder'
INVALID_FOLDER_NAME = 'invalidFolder'
VALID_EXECUTION_ID = 1
INVALID_EXECUTION_ID = 0
VALID_ASSIGNEE = 'arthur.king'
INVALID_ASSIGNEE = 'sirNotAppearingInThisFilm'


class TestResource(ZephyrTestCase):
    def test_init(self):
        name = 'foo'
        id_ = 1
        resource = Resource(name=name, id_=id_, session=self.zephyr_client)
        self.assertEqual(resource.name, name)
        self.assertEqual(resource.id_, id_)
        self.assertEqual(resource.zephyr_session, self.zephyr_client)

class TestProject(ZephyrTestCase):
    def setUp(self):
        super().setUp()
        self.project = Project()

    def test_init(self):
        name = 'foo'
        id_ = 1
        project = Project(name=name, id_=id_, session=self.zephyr_client)
        expected_url = self.zephyr_client.server + '/rest/api/2/project/1'
        self.assertEqual(project.url, expected_url)
        self.assertIsNone(project._versions)
    
    def test_versions(self):
        """ TODO: need to mock responses for this to work"""
        self.assertIsInstance(self.project.versions, list)  # When accessed, versions returns a list

    def test_version(self):
        """ TODO: need to mock responses for this to work"""
        version = self.project.version(VALID_VERSION_NAME)
        self.assertIsInstance(version, Version)

class TestVersion(ZephyrTestCase):
    def setUp(self):
        super().setUp()
        self.version = Version()

    def test_init(self):
        name = 'foo'
        id_ = 1
        project = 2
        version = Version(project=project, name=name, id_=id_, session=self.zephyr_client)
        self.assertEqual(version.project, project)
        self.assertIsNone(version._cycles)

    def test_cycles(self):
        self.assertIsInstance(self.version.cycles, list)

    def test_cycle(self):
        cycle = self.version.cycle(VALID_CYCLE_NAME)
        self.assertIsInstance(cycle, Cycle)

class TestCycle(ZephyrTestCase):
    def setUp(self):
        super().setUp()
        self.cycle = Cycle()

    def test_init(self):
        name = 'foo'
        id_ = 1
        project = 2
        version = 3
        expected_id = 4 # TODO: determined by mock?
        expected_url = self.zephyr_client.server + '/cycle/' + expected_id
        cycle = Cycle(name=name, id_=id_, session=self.zephyr_client, project=project, version=version)
        self.assertEqual(cycle.name, name)
        self.assertEqual(cycle.id_, id_)
        self.assertEqual(cycle.project, project)
        self.assertEqual(cycle.version, version)
        self.assertEqual(cycle.url, expected_url)
        self.assertIsNone(cycle._folders)

    def test_folders(self):
        self.assertIsInstance(self.cycle.folders, list)
        self.assertIsInstance(self.cycle._folders, list)

    def test_folder(self):
        folder = self.cycle.folder(VALID_FOLDER_NAME)
        self.assertIsInstance(folder, Folder)
        with self.assertRaises(KeyError):
            self.cycle.folder(INVALID_FOLDER_NAME)

class TestFolder(ZephyrTestCase):
    def setUp(self):
        super().setUp()
        self.folder = Folder()

    def test_init(self):
        raise NotImplementedError

class TestExecution(ZephyrTestCase):
    def setUp(self):
        super().setUp()
        self.execution = Execution()

    def test_init(self):
        raise NotImplementedError

    def test_raw(self):
        self.assertIsNone(self.execution._raw)
        self.assertIsInstance(self.execution.raw, dict)
        self.assertIsInstance(self.execution._raw, dict)

    def test_steps(self):
        self.assertIsNone(self.execution._steps)
        self.assertIsInstance(self.execution.steps, list)
        self.assertIsInstance(self.execution._steps, list)

    def test_assign(self):
        assignee = VALID_ASSIGNEE
        invalid_assignee = INVALID_ASSIGNEE
        self.assertNotEqual(self.execution.assignee, assignee)
        self.execution.assign(assignee)
        self.assertEqual(self.execution.assignee, assignee)
        with self.assertRaises(ValueError):
            self.execution.assign(invalid_assignee)

    def test_update(self):
        status = execution_status.WIP
        comment = 'foo'
        self.assertNotEqual(self.execution.status, status)
        self.execution.update(status=status, comment=comment)
        self.assertEqual(self.execution.status, status)
        self.assertEqual(self.execution.comment, comment)

if __name__ == '__main__':
    unittest.main()
