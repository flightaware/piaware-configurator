import pytest 

def pytest_addoption(parser):
    parser.addoption(
        '--base-url', action='store', default='http://172.16.32.89/', help='Base URL for the API tests'
    )

@pytest.fixture()
def get_base_url(request):
    baseURL = request.config.getoption('--base-url')
    print(baseURL)
    return baseURL