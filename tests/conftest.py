def pytest_addoption(parser):
    parser.addoption(
        "--dirs", 
        action="store", 
        default=None, 
        help="Comma-separated list of directories to test Docker builds in"
    )
    