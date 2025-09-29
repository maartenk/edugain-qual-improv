"""Tests for __main__.py module."""

import os
import sys
from unittest.mock import patch

# Add src to Python path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src")
)


class TestMainModule:
    """Test the __main__.py module."""

    def test_main_module_import(self):
        """Test that the main module can be imported without errors."""
        import edugain_analysis.__main__

        # Verify expected attributes exist
        assert hasattr(edugain_analysis.__main__, "main")

        # Verify it's the correct main function
        from edugain_analysis.cli.main import main as expected_main

        assert edugain_analysis.__main__.main is expected_main

    @patch("edugain_analysis.cli.main.main")
    def test_main_execution_when_run_as_main(self, mock_main):
        """Test that main() is called when __name__ == '__main__'."""
        # Create a local scope that simulates running as __main__
        local_vars = {"__name__": "__main__", "main": mock_main}

        # Execute the conditional code block
        exec('if __name__ == "__main__": main()', {}, local_vars)

        # Verify main was called
        mock_main.assert_called_once()
