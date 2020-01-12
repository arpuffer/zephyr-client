import unittest
from unittest import TestCase, mock
from typing import Union

from requests.exceptions import Timeout
from jira import JIRAError
from requests.exceptions import ConnectionError

from zephyr import Zephyr
from zephyr.resources import Project, Execution, Folder
from .mocks import (VALID_SERVER,
                    INVALID_SERVER,
                    VALID_ZQL_QUERY,
                    INVALID_ZQL_QUERY,
                    EMPTY_ZQL_QUERY,
                    mocked_get,
                    mocked_get_invalid_auth,
                    mocked_load_projects,
                    mocked_put)

ZAPI_URL = '{}/rest/zapi/latest/'
CHECK_CONNECTION_URL = '{}cycle?expand='.format(ZAPI_URL)

VALID_PROJECT = 'validproject'
INVALID_PROJECT = 'invalidproject'
SEARCH_ZQL = ZAPI_URL + 'zql/executeSearch?zqlQuery={}'
EMPTY_ZQL = ''  # TODO
INVALID_ZQL = 'also wik' # TODO
VALID_EXECUTION_ID = 0  # TODO

class ZephyrTestCase(TestCase):
    @mock.patch('requests.Session.get', side_effect=mocked_get)
    def setUp(self, mock_get):
        self.zephyr_client = Zephyr(server=VALID_SERVER)

class TestClient(ZephyrTestCase):
    @mock.patch('requests.Session.get', side_effect=mocked_get)
    def test_init_valid(self, mock_get):
        server = VALID_SERVER
        auth = ('Foo', 'Bar')
        verify = False
        timeout = 13
        client = Zephyr(server=server,
                        basic_auth=auth,
                        verify=verify,
                        timeout=timeout)
        self.assertEqual(client.server, server)
        self.assertEqual(client._session.auth, auth)
        self.assertEqual(client._session.verify, verify)
        self.assertEqual(client.timeout, timeout)
        self.assertIsNone(client._projects)  # Verify projects cache is None, to be loaded upon access of 'projects'

    @mock.patch('requests.Session.get', side_effect=mocked_get)
    def test_init_invalid_server(self, mock_get):
        server = INVALID_SERVER
        with self.assertRaises(ConnectionError):
            Zephyr(server=server)

    @mock.patch('requests.Session.get', side_effect=mocked_get_invalid_auth)
    def test_init_invalid_auth(self, mock_get):
        with self.assertRaises(JIRAError):
            Zephyr()
    
    @mock.patch('zephyr.Zephyr._load_projects', side_effect=['Foo', 'Bar'])
    def test_projects_loading(self, mock_load_projects):
        """Zephyr Client attr: projects is lazily loaded.
        Test for initialization as NoneType is executed in the init test.
        On call of attr: projects, load function is executed.  Afterward,
        the typeof attr: projects should be a list
        """
        self.zephyr_client._load_projects()
        projects = self.zephyr_client.projects
        self.assertIsInstance(projects, list)

    def test_project_valid(self):
        """Calling project() with valid project name returns a Project
        Calling it with an invalid project name raises a JIRAError
        """
        PROJECTS = [Project(name=VALID_PROJECT, id_=1, session=self.zephyr_client),
                    Project(name='Foo', id_=2, session=self.zephyr_client)]
        self.zephyr_client._projects = PROJECTS[:]
        project = self.zephyr_client.project(VALID_PROJECT)
        self.assertEqual(VALID_PROJECT, project.name)
        with self.assertRaises(JIRAError):
            self.zephyr_client.project(INVALID_PROJECT)

    @mock.patch('requests.Session.get', side_effect=mocked_get)
    def test_executions_zql(self, mock_get):
        query_result = self.zephyr_client.executions_zql(VALID_ZQL_QUERY)
        self.assertIsInstance(query_result, (list, Execution))
        query_result = self.zephyr_client.executions_zql(EMPTY_ZQL_QUERY)
        self.assertIsInstance(query_result, list)
        with self.assertRaises(JIRAError):
            self.zephyr_client.executions_zql(INVALID_ZQL_QUERY)

    @mock.patch('zephyr.Zephyr.put', side_effect=mocked_put)
    def test_move_executions_url(self, mock_put):
        executions = [Execution(1, self.zephyr_client),
                      Execution(2, self.zephyr_client)]
        ID_ = 1
        PROJECT = 2
        VERSION = 3
        CYCLE = 4
        URL = self.zephyr_client.server + '/rest/zapi/latest/cycle/4/move/executions/folder/1'
        DATA = '{"projectId": 2, "versionId": 3, "schedulesList": [1, 2]}'
        dest_folder = Folder(name = 'testFolder',
                             id_ = ID_,
                             project=PROJECT,
                             version=VERSION,
                             cycle=CYCLE,
                             session=self.zephyr_client)
        try:
            self.zephyr_client.move_executions(executions=executions, destination_folder=dest_folder)
        finally:
            mock_put.assert_called_with(url=URL, data=DATA)

    @mock.patch('requests.Session.get')
    def test_get(self, mock_get):
        """Zephyr.get() passes url, timeout, params to requests.Session.get()"""
        url = 'Foo'
        params = {'foo': 'bar'}
        timeout = self.zephyr_client.timeout
        self.zephyr_client.get(url=url, params=params, raise_for_error=False)
        mock_get.assert_called_with(url=url, timeout=timeout, params=params)

    @mock.patch('requests.Session.put')
    def test_put(self, mock_put):
        """Zephyr.put() passes url and params
        through to a requests.Session.put() 
        """
        url = 'Foo'
        data = '{"demand": "shrubbery"}'
        self.zephyr_client.put(url=url, data=data, raise_for_error=False)
        mock_put.assert_called_with(url=url, timeout=self.zephyr_client.timeout, data=data)

if __name__ == '__main__':
    unittest.main()
