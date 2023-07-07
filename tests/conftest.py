def pytest_addoption(parser):
    parser.addoption(
        "--g",
        help="generate mock responses",
        action="store_true"
    )