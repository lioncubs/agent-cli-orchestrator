"""Context manager for injecting session history into prompts."""

from typing import Optional, List
from src.session.models import Session, Turn


class ContextManager:
    """
    Manages context injection for prompts.
    
    Handles injecting session history and other context into prompts
    to maintain conversation continuity.
    """
    
    def __init__(self, max_turns: int = 10, max_chars_per_turn: int = 2000):
        """
        Initialize context manager.
        
        Args:
            max_turns: Maximum number of recent turns to include
            max_chars_per_turn: Maximum characters per turn summary
        """
        self.max_turns = max_turns
        self.max_chars_per_turn = max_chars_per_turn
    
    def build_context(
        self,
        session: Session,
        current_prompt: str,
        include_files: bool = True
    ) -> str:
        """
        Build a context-enriched prompt from session history.
        
        Args:
            session: Session containing conversation history
            current_prompt: The new prompt to send
            include_files: Whether to include file change information
            
        Returns:
            Context-enriched prompt string
        """
        context_parts = []
        
        # Add session metadata
        context_parts.append(f"Session Type: {session.type.value}")
        context_parts.append(f"Repository: {session.repo_name}")
        
        if session.base_branch:
            context_parts.append(f"Base Branch: {session.base_branch}")
        
        # Add conversation history
        if session.turns:
            context_parts.append("\n--- Previous Conversation ---")
            recent_turns = self._get_recent_turns(session.turns)
            
            for turn in recent_turns:
                context_parts.append(f"\nTurn {turn.id}:")
                context_parts.append(f"User: {self._truncate(turn.prompt, self.max_chars_per_turn)}")
                context_parts.append(f"Assistant: {self._truncate(turn.response_summary, self.max_chars_per_turn)}")
                
                if include_files and (turn.files_analyzed or turn.files_changed):
                    if turn.files_analyzed:
                        context_parts.append(f"  Files analyzed: {', '.join(turn.files_analyzed[:5])}")
                    if turn.files_changed:
                        context_parts.append(f"  Files changed: {', '.join(turn.files_changed[:5])}")
        
        # Add summary of all file changes in session
        if include_files and session.files_changed:
            context_parts.append(f"\n--- Files Changed in Session ---")
            context_parts.append(", ".join(session.files_changed[:20]))
        
        # Add current prompt
        context_parts.append("\n--- Current Request ---")
        context_parts.append(current_prompt)
        
        return "\n".join(context_parts)
    
    def build_simple_context(self, session: Session, current_prompt: str) -> str:
        """
        Build a minimal context from just the last turn.
        
        Args:
            session: Session containing conversation history
            current_prompt: The new prompt to send
            
        Returns:
            Minimal context string
        """
        if not session.turns:
            return current_prompt
        
        last_turn = session.turns[-1]
        context = f"Previous: {self._truncate(last_turn.response_summary, 500)}\n\nCurrent: {current_prompt}"
        return context
    
    def extract_files_from_response(self, response: str) -> List[str]:
        """
        Extract file paths mentioned in a response.
        
        This is a simple implementation that looks for common file patterns.
        A more sophisticated version could use AST parsing or LLM extraction.
        
        Args:
            response: Response text to analyze
            
        Returns:
            List of file paths found
        """
        import re
        
        # Pattern for common file paths
        # Matches things like: src/file.py, /path/to/file.js, ./relative/path.txt
        file_pattern = r'(?:\.{0,2}/)?(?:[\w\-]+/)*[\w\-]+\.[\w]+'
        
        matches = re.findall(file_pattern, response)
        
        # Filter out common false positives
        excluded_extensions = {'com', 'org', 'io', 'net', 'html', 'http', 'https'}
        files = []
        for match in matches:
            ext = match.split('.')[-1].lower()
            if ext not in excluded_extensions and len(match) < 200:
                files.append(match)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for f in files:
            if f not in seen:
                seen.add(f)
                unique_files.append(f)
        
        return unique_files
    
    def _get_recent_turns(self, turns: List[Turn]) -> List[Turn]:
        """
        Get the most recent turns up to max_turns.
        
        Args:
            turns: All turns in the session
            
        Returns:
            List of recent turns
        """
        if len(turns) <= self.max_turns:
            return turns
        return turns[-self.max_turns:]
    
    def _truncate(self, text: str, max_length: int) -> str:
        """
        Truncate text to maximum length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
