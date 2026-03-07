import pytest
from unittest.mock import patch

from stt2vtt.cli import main


@patch('sys.argv', ['stt2vtt', '--help'])
def test_help():
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
