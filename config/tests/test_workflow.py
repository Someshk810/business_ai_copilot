"""Tests for agent workflows."""

import unittest
from src.agent.orchestrator import AgentOrchestrator
from src.agent.state import AgentState


class TestAgentOrchestrator(unittest.TestCase):
    """Tests for AgentOrchestrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = AgentOrchestrator()
    
    def test_initialize(self):
        """Test orchestrator initialization."""
        self.orchestrator.initialize()
        self.assertIsNotNone(self.orchestrator.state)


class TestAgentState(unittest.TestCase):
    """Tests for AgentState."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.state = AgentState()
    
    def test_add_message(self):
        """Test adding messages to state."""
        self.state.add_message("user", "Hello")
        self.assertEqual(len(self.state.messages), 1)
        self.assertEqual(self.state.messages[0]["content"], "Hello")
    
    def test_add_error(self):
        """Test adding errors to state."""
        self.state.add_error("Test error")
        self.assertEqual(len(self.state.errors), 1)
        self.assertIn("Test error", self.state.errors)


if __name__ == "__main__":
    unittest.main()
