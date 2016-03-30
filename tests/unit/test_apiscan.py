"""Unit tests for the apiscan module of the coprcheck package."""

import pytest
import re
import requests
import responses

from coprcheck import apiscan as ascn


# ### Common test data ###
PROJECT_SCHEMA = 'user,project'
VALID_PROJECTS = [('jstanek','udiskie'),]
INVALID_PROJECTS = [('nobody', 'nothing'),]

for_all_projects = pytest.mark.parametrize(
        PROJECT_SCHEMA, VALID_PROJECTS+INVALID_PROJECTS)

for_valid_projects = pytest.mark.parametrize(
        PROJECT_SCHEMA, VALID_PROJECTS)

for_invalid_projects = pytest.mark.parametrize(
        PROJECT_SCHEMA, INVALID_PROJECTS)

# ### Fixtures ###
@pytest.fixture
def mock_requests():
    """Mocked requests library."""
    return responses.RequestsMock()

@pytest.fixture
def mock_no_connectivity(mock_requests):
    """Mocked requests to always raise ConnectionError."""
    mock_requests.add(responses.GET, re.compile('.*'),
                      body=requests.ConnectionError('No connectivity!'))
    return mock_requests

@pytest.fixture
def mock_monitor(mock_requests):
    """Mocked response from COPR monitor."""
    url = lambda u, p: ''.join([
            ascn.COPR_ROOT, ascn.MONITOR_URL.format(user=u, project=p)])

    for user, project in VALID_PROJECTS:
        mock_requests.add(
                responses.GET, url(user, project),
                status=200, json={'status': 'succeeded'})

    for user, project in INVALID_PROJECTS:
        mock_requests.add(
                responses.GET, url(user, project),
                status=404,
                json={'status': 'failed', 'error': 'NotFound'})

    mock_requests.assert_all_requests_are_fired = False
    return mock_requests

# ### Monitor tests ###

@for_valid_projects
def test_monitor_success(mock_monitor, user, project):
    with mock_monitor:
        assert ascn.monitor(user, project) == {'status': 'succeeded'}

@for_all_projects
def test_monitor_no_connectivity(mock_no_connectivity, user, project):
    with mock_no_connectivity, pytest.raises(ascn.ConnectionError):
        ascn.monitor(user, project)

@for_invalid_projects
def test_monitor_no_project(mock_monitor, user, project):
    with mock_monitor, pytest.raises(ascn.ProjectNotFoundError):
        ascn.monitor(user, project)
