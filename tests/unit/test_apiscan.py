"""Unit tests for the apiscan module of the coprcheck package."""

from collections import namedtuple
import re

import pytest
import requests
import responses

from coprcheck import apiscan as ascn


# ### Tools for parametrization ###
MockData = namedtuple('MockData', ['scheme', 'valid', 'invalid'])
"""Structure of mock test data/parametres."""

ParameterDecorators = namedtuple('ParameterDecorators', ['all', 'valid', 'invalid'])
"""Set of decorators for passing parameters to tests."""

def make_param_decorators(data: MockData) -> ParameterDecorators:
    """Create decorators from test data."""
    return ParameterDecorators(
            all=pytest.mark.parametrize(data.scheme, data.valid+data.invalid),
            valid=pytest.mark.parametrize(data.scheme, data.valid),
            invalid=pytest.mark.parametrize(data.scheme, data.invalid))

# ### Common test data ###
MOCK_PROJECTS = MockData(
        scheme='user,project',
        valid=[('jstanek', 'udiskie')],
        invalid=[('nobody', 'nothing')])
for_projects = make_param_decorators(MOCK_PROJECTS)

MOCK_BUILDS = MockData(
        scheme='build_id',
        valid=[42],
        invalid=[99])
for_builds = make_param_decorators(MOCK_BUILDS)

# ### Fixtures ###
@pytest.fixture
def mock_no_connectivity():
    """Mocked requests to always raise ConnectionError."""

    mock_requests = responses.RequestsMock()
    mock_requests.add(responses.GET, re.compile('.*'),
                      body=requests.ConnectionError('No connectivity!'))
    return mock_requests

# ### Monitor tests ###

MONITOR_URL = ascn.COPR_ROOT + ascn.MONITOR_URL

@for_projects.valid
@responses.activate
def test_monitor_success(user, project):
    responses.add(responses.GET, url=MONITOR_URL.format(user=user, project=project),
                  status=200, json={'builds': []})

    monitor_data = ascn.monitor(user, project)
    assert 'builds' in monitor_data

@for_projects.all
def test_monitor_no_connectivity(mock_no_connectivity, user, project):
    with mock_no_connectivity, pytest.raises(ascn.ConnectionError):
        monitor_data = ascn.monitor(user, project)

@for_projects.invalid
@responses.activate
def test_monitor_no_project(user, project):
    responses.add(responses.GET, url=MONITOR_URL.format(user=user, project=project),
                  status=404, json={'error': 'Project does not exists.'})

    with pytest.raises(ascn.ProjectNotFoundError):
        monitor_data = ascn.monitor(user, project)

@for_projects.all
@responses.activate
def test_monitor_server_error(user, project):
    responses.add(responses.GET, url=MONITOR_URL.format(user=user, project=project),
                  status=500, content_type='test/plain',
                  body='500 Internal Server Error')

    with pytest.raises(ascn.HTTPError):
        monitor_data = ascn.monitor(user, project)

# ### Build tests ###

BUILD_URL = ascn.COPR_ROOT + ascn.BUILD_URL

@for_builds.valid
@responses.activate
def test_build_success(build_id):
    responses.add(responses.GET, url=BUILD_URL.format(build_id=build_id),
                  status=200, json={'build': {}})

    build_data = ascn.build(build_id)
    print(responses.calls[0])
    assert 'build' in build_data

@for_builds.all
def test_build_no_connectivity(mock_no_connectivity, build_id):
    with mock_no_connectivity, pytest.raises(ascn.ConnectionError):
        build_data = ascn.build(build_id)

@for_builds.invalid
@responses.activate
def test_build_nonexistent(build_id):
    responses.add(responses.GET, url=BUILD_URL.format(build_id=build_id),
                  status=404, json={'message': 'Build not found.'})

    with pytest.raises(ascn.BuildNotFoundError):
        build_data = ascn.build(build_id)

@for_builds.all
@responses.activate
def test_build_server_error(build_id):
    responses.add(responses.GET, url=BUILD_URL.format(build_id=build_id),
                  status=500, content_type='text/plain',
                  body='500 Internal Server Error')

    with pytest.raises(ascn.HTTPError):
        build_data = ascn.build(build_id)
