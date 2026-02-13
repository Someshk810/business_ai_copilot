"""Tests for agent tools."""

import unittest
from src.tools.project_status import ProjectStatusTool
from src.tools.knowledge_search import KnowledgeSearchTool
from src.tools.email_composer import EmailComposerTool


class TestProjectStatusTool(unittest.TestCase):
    """Tests for ProjectStatusTool."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tool = ProjectStatusTool()
    
    def test_execute(self):
        """Test tool execution."""
        result = self.tool.execute(project_id="TEST-001")
        self.assertIn("project_id", result)
        self.assertIn("status", result)


class TestKnowledgeSearchTool(unittest.TestCase):
    """Tests for KnowledgeSearchTool."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tool = KnowledgeSearchTool()
    
    def test_execute(self):
        """Test tool execution."""
        result = self.tool.execute(query="test query")
        self.assertIn("query", result)
        self.assertIn("results", result)


class TestEmailComposerTool(unittest.TestCase):
    """Tests for EmailComposerTool."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tool = EmailComposerTool()
    
    def test_execute(self):
        """Test tool execution."""
        result = self.tool.execute(
            recipients=["test@example.com"],
            subject="Test",
            body="Test body"
        )
        self.assertIn("recipients", result)
        self.assertIn("status", result)


if __name__ == "__main__":
    unittest.main()
