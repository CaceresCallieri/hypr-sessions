"""
Session Window Calculator Component

Calculates visible session windows and scroll indicators for efficient display
of large session collections. Extracted from BrowsePanelWidget for reusability.
"""

from typing import List, Optional

from utils import VISIBLE_WINDOW_SIZE


class SessionWindowCalculator:
    """Calculates visible session windows and scroll indicators"""

    def __init__(self, window_size: int = VISIBLE_WINDOW_SIZE):
        """Initialize the window calculator
        
        Args:
            window_size: Number of sessions to show in the visible window
        """
        self.window_size = window_size
        self.visible_start_index = 0

    def calculate_visible_window(self, filtered_sessions: List[str], 
                               selected_session: Optional[str] = None) -> List[int]:
        """Calculate which sessions should be visible based on current selection and filtering
        
        Args:
            filtered_sessions: List of filtered session names
            selected_session: Currently selected session name (optional)
            
        Returns:
            List of indices for sessions that should be visible
        """
        total_filtered = len(filtered_sessions)

        # Early return for simple case - all sessions fit in window
        if total_filtered <= self.window_size:
            self.visible_start_index = 0
            return list(range(total_filtered))

        # Calculate optimal window position based on selection
        selected_index = self._get_selected_filtered_index(filtered_sessions, selected_session)
        optimal_start = self._calculate_optimal_window_start(selected_index)
        self.visible_start_index = self._clamp_to_valid_bounds(optimal_start, total_filtered)

        return self._get_visible_indices_range(total_filtered)

    def get_visible_sessions(self, filtered_sessions: List[str], 
                           selected_session: Optional[str] = None) -> List[str]:
        """Get the list of sessions that should be currently visible
        
        Args:
            filtered_sessions: List of filtered session names
            selected_session: Currently selected session name (optional)
            
        Returns:
            List of session names that should be visible
        """
        visible_indices = self.calculate_visible_window(filtered_sessions, selected_session)
        return [filtered_sessions[i] for i in visible_indices]

    def has_sessions_above(self) -> bool:
        """Check if there are sessions above the visible window
        
        Returns:
            True if there are sessions above the current window
        """
        return self.visible_start_index > 0

    def has_sessions_below(self, total_sessions: int) -> bool:
        """Check if there are sessions below the visible window
        
        Args:
            total_sessions: Total number of filtered sessions
            
        Returns:
            True if there are sessions below the current window
        """
        return (self.visible_start_index + self.window_size) < total_sessions

    def get_next_selection_index(self, filtered_sessions: List[str], 
                                selected_session: Optional[str]) -> int:
        """Calculate next session index with wraparound
        
        Args:
            filtered_sessions: List of filtered session names
            selected_session: Currently selected session name
            
        Returns:
            Index of next session to select
        """
        if not filtered_sessions:
            return 0
            
        current_idx = self._get_selected_filtered_index(filtered_sessions, selected_session)
        return (current_idx + 1) % len(filtered_sessions)

    def get_previous_selection_index(self, filtered_sessions: List[str], 
                                   selected_session: Optional[str]) -> int:
        """Calculate previous session index with wraparound
        
        Args:
            filtered_sessions: List of filtered session names
            selected_session: Currently selected session name
            
        Returns:
            Index of previous session to select
        """
        if not filtered_sessions:
            return 0
            
        current_idx = self._get_selected_filtered_index(filtered_sessions, selected_session)
        return (current_idx - 1) % len(filtered_sessions)

    def _get_selected_filtered_index(self, filtered_sessions: List[str], 
                                   selected_session: Optional[str]) -> int:
        """Get index of selected session in filtered results, or 0 if none
        
        Args:
            filtered_sessions: List of filtered session names
            selected_session: Currently selected session name
            
        Returns:
            Index of selected session, or 0 if not found
        """
        if selected_session and selected_session in filtered_sessions:
            return filtered_sessions.index(selected_session)
        return 0

    def _calculate_optimal_window_start(self, selected_index: int) -> int:
        """Calculate ideal window start position for given selection
        
        Args:
            selected_index: Index of selected session (must be >= 0)
            
        Returns:
            Optimal window start position
            
        Example:
            If selected_index=7, window_size=5, current_start=0
            Returns: 3 (positions selection in window at indices 3-7)
            
        Raises:
            ValueError: If selected_index is invalid
        """
        if not isinstance(selected_index, int) or selected_index < 0:
            raise ValueError(f"selected_index must be non-negative integer, got {selected_index}")
        
        window_end = self.visible_start_index + self.window_size

        if selected_index < self.visible_start_index:
            # Selection is above visible window
            return selected_index
        elif selected_index >= window_end:
            # Selection is below visible window
            return selected_index - self.window_size + 1
        else:
            # Selection is within current window - no change needed
            return self.visible_start_index

    def _clamp_to_valid_bounds(self, window_start: int, total_sessions: int) -> int:
        """Ensure window position stays within valid bounds
        
        Args:
            window_start: Proposed window start position
            total_sessions: Total number of sessions (must be >= 0)
            
        Returns:
            Clamped window start position within valid bounds
            
        Example:
            If window_start=10, total_sessions=8, window_size=5
            Returns: 3 (maximum valid start for 8 sessions)
            
        Raises:
            ValueError: If arguments are invalid
        """
        if not isinstance(total_sessions, int) or total_sessions < 0:
            raise ValueError(f"total_sessions must be non-negative integer, got {total_sessions}")
        
        if not isinstance(window_start, int):
            raise ValueError(f"window_start must be integer, got {window_start}")
        
        clamped = min(window_start, total_sessions - self.window_size)
        return max(0, clamped)

    def _get_visible_indices_range(self, total_sessions: int) -> List[int]:
        """Generate list of visible session indices
        
        Args:
            total_sessions: Total number of sessions (must be >= 0)
            
        Returns:
            List of indices for sessions visible in current window
            
        Example:
            If visible_start_index=2, window_size=5, total_sessions=10
            Returns: [2, 3, 4, 5, 6]
            
        Raises:
            ValueError: If total_sessions is invalid
        """
        if not isinstance(total_sessions, int) or total_sessions < 0:
            raise ValueError(f"total_sessions must be non-negative integer, got {total_sessions}")
            
        window_end = min(self.visible_start_index + self.window_size, total_sessions)
        return list(range(self.visible_start_index, window_end))

    def reset_position(self):
        """Reset window position to the beginning"""
        self.visible_start_index = 0