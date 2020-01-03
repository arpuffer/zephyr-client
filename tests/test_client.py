import unittest
from typing import Union
from requests.exceptions import Timeout
from ..src.zephyr import Zephyr
from ..src.zephyr.resources import Project, Execution, Folder

INVALID_SERVER = 'invalid'
VALID_SERVER = 'valid'
INVALID_AUTH = ('invalid', 'invalid')
VALID_AUTH = ('valid', 'valid')
VALID_PROJECT = 'valid'
INVALID_PROJECT = 'invalid'
POPULATED_ZQL = '' # TODO
EMPTY_ZQL = ''  # TODO
INVALID_ZQL = 'also wik' # TODO
VALID_EXECUTION_ID = 0  # TODO
EMPTY_FOLDER = Folder()

class ZephyrTestCase(unittest.TestCase):
    def setUp(self):
        self.zephyr_client = Zephyr()

class TestClient(ZephyrTestCase):
    def test_init_valid(self):
        server = VALID_SERVER
        auth = VALID_AUTH
        verify = False
        timeout = 13
        client = Zephyr()
        self.assertEqual(client.server, server)
        self.assertEqual(client.auth, auth)
        self.assertEqual(client.verify, verify)
        self.assertEqual(client.timeout, timeout)
        self.assertIsNone(client._projects)  # Verify projects cache is None, to be loaded upon access of 'projects'

    def test_init_invalid_server(self):
        server = INVALID_SERVER
        with self.assertRaises(Timeout):
            Zephyr(server=server)

    def test_init_invalid_auth(self):
        auth = INVALID_AUTH
        with self.assertRaises(ValueError):
            Zephyr(basic_auth = auth)
    
    def test_projects_loading(self):
        """Zephyr Client attr: projects is lazily loaded.
        Test for initialization as NoneType is executed in the init test.
        On call of attr: projects, load function is executed.  Afterward,
        the typeof attr: projects should be a list
        """
        self.assertIsInstance(self.zephyr_client.projects, list)

    def test_project_valid(self):
        project = self.zephyr_client.project(VALID_PROJECT)
        self.assertIsInstance(project, Project)

    def test_project_invalid(self):
        with self.assertRaises(KeyError):
            self.zephyr_client.project(INVALID_PROJECT)

    def test_executions_zql_valid(self):
        query_result = self.zephyr_client.executions_zql(POPULATED_ZQL)
        self.assertIsInstance(query_result, Union[list, Execution])
        query_result = self.zephyr_client.executions_zql(EMPTY_ZQL)
        self.assertIsInstance(query_result, list)
        with self.assertRaises(ValueError):
            self.zephyr_client.executions_zql(INVALID_ZQL)

    def test_move_executions(self):
        execution = Execution(VALID_EXECUTION_ID, self.zephyr_client)
        orig_folder_id = execution.folder_id
        dest_folder = EMPTY_FOLDER
        self.assertNotEqual(orig_folder_id, dest_folder.id_)
        self.assertNotEqual(dest_folder.id_, execution.folder_id)
        self.zephyr_client.move_executions(executions=[execution], destination_folder=dest_folder)
        self.assertEqual(dest_folder.id_, execution.folder_id)

    def test_get(self):
        """Given a Zephyr.get() call, url and params are passed
        through to a requests.Session.get() call -- TODO: use mocks?
        """
        self.assertTrue(False, 'TODO: BEHAVIOR NOT OUTLINED')

    def test_put(self):
        """Given a Zephyr.put() call, url and params are passed
        through to a requests.Session.put() call -- TODO: use mocks?
        """
        self.assertTrue(False, 'TODO: BEHAVIOR NOT OUTLINED')

    def test_post(self):
        """Given a Zephyr.post() call, url and params are passed
        through to a requests.Session.post() call -- TODO: use mocks?
        """
        self.assertTrue(False, 'TODO: BEHAVIOR NOT OUTLINED')

if __name__ == '__main__':
    unittest.main()
