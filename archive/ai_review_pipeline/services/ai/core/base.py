"""
Base Classes for AI Services

This module contains base classes and common functionality for AI services
in the Community Resource Directory.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from django.conf import settings


class BaseAIService(ABC):
    """Base class for all AI services."""
    
    def __init__(self, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = getattr(settings, 'AI_SERVICE_CONFIG', {})
        self._setup_service(**kwargs)
    
    def _setup_service(self, **kwargs):
        """Setup the service with configuration."""
        pass
    
    @abstractmethod
    def process(self, data: Any) -> Dict[str, Any]:
        """Process data and return results."""
        pass
    
    def validate_input(self, data: Any) -> bool:
        """Validate input data."""
        return True
    
    def log_activity(self, message: str, level: str = 'info'):
        """Log service activity."""
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(f"[{self.__class__.__name__}] {message}")


class BaseAIReviewService(BaseAIService):
    """Base class for AI review services."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.review_config = self.config.get('review', {})
    
    @abstractmethod
    def review_resource(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """Review a resource and return review results."""
        pass
    
    def validate_resource_data(self, resource_data: Dict[str, Any]) -> bool:
        """Validate resource data for review."""
        required_fields = ['name', 'description']
        return all(field in resource_data for field in required_fields)


class BaseAIReportService(BaseAIService):
    """Base class for AI report services."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.report_config = self.config.get('reports', {})
    
    @abstractmethod
    def generate_report(self, data: Any, report_type: str) -> Dict[str, Any]:
        """Generate a report based on data and type."""
        pass
    
    def format_report(self, report_data: Dict[str, Any]) -> str:
        """Format report data for output."""
        return str(report_data)


class BaseAITool(BaseAIService):
    """Base class for AI tools."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tool_config = self.config.get('tools', {})
    
    @abstractmethod
    def execute(self, input_data: Any) -> Dict[str, Any]:
        """Execute the tool with input data."""
        pass
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Get information about the tool."""
        return {
            'name': self.__class__.__name__,
            'description': getattr(self, '__doc__', ''),
            'version': getattr(self, '__version__', '1.0.0')
        }
