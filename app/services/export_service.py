"""
Export Service - Handle data export in various formats
"""

import json
import csv
import io
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    PDF = "pdf"
    HTML = "html"


class ExportService:
    """Service for exporting data in various formats."""
    
    def __init__(self):
        """Initialize export service."""
        self.export_history: List[Dict] = []
    
    def export_to_json(
        self,
        data: Any,
        pretty: bool = True,
        filename: Optional[str] = None
    ) -> str:
        """
        Export data to JSON format.
        
        Args:
            data: Data to export
            pretty: Use pretty printing
            filename: Optional filename for metadata
            
        Returns:
            JSON string
        """
        try:
            if pretty:
                json_str = json.dumps(data, indent=2, default=str)
            else:
                json_str = json.dumps(data, default=str)
            
            self._record_export(ExportFormat.JSON, filename)
            logger.info(f"Exported data to JSON")
            return json_str
            
        except Exception as e:
            logger.error(f"JSON export failed: {str(e)}")
            raise
    
    def export_to_csv(
        self,
        data: List[Dict],
        columns: Optional[List[str]] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Export data to CSV format.
        
        Args:
            data: List of dictionaries to export
            columns: Column names (if None, use keys from first dict)
            filename: Optional filename for metadata
            
        Returns:
            CSV string
        """
        try:
            if not data:
                return ""
            
            # Determine columns
            if columns is None:
                columns = list(data[0].keys())
            
            # Create CSV
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)
            
            csv_str = output.getvalue()
            output.close()
            
            self._record_export(ExportFormat.CSV, filename)
            logger.info(f"Exported {len(data)} rows to CSV")
            return csv_str
            
        except Exception as e:
            logger.error(f"CSV export failed: {str(e)}")
            raise
    
    def export_to_markdown(
        self,
        data: Any,
        title: Optional[str] = None,
        include_metadata: bool = True,
        filename: Optional[str] = None
    ) -> str:
        """
        Export data to Markdown format.
        
        Args:
            data: Data to export
            title: Document title
            include_metadata: Include export metadata
            filename: Optional filename for metadata
            
        Returns:
            Markdown string
        """
        try:
            lines = []
            
            # Title
            if title:
                lines.append(f"# {title}\n")
            
            # Metadata
            if include_metadata:
                lines.append(f"*Exported: {datetime.now().isoformat()}*\n")
            
            # Data
            if isinstance(data, list):
                for i, item in enumerate(data, 1):
                    lines.append(f"## Item {i}\n")
                    if isinstance(item, dict):
                        for key, value in item.items():
                            lines.append(f"- **{key}**: {value}")
                    else:
                        lines.append(str(item))
                    lines.append("")
            elif isinstance(data, dict):
                for key, value in data.items():
                    lines.append(f"## {key}\n")
                    lines.append(str(value))
                    lines.append("")
            else:
                lines.append(str(data))
            
            markdown_str = "\n".join(lines)
            
            self._record_export(ExportFormat.MARKDOWN, filename)
            logger.info("Exported data to Markdown")
            return markdown_str
            
        except Exception as e:
            logger.error(f"Markdown export failed: {str(e)}")
            raise
    
    def export_tasks(
        self,
        tasks: List[Dict],
        format: ExportFormat = ExportFormat.JSON,
        **kwargs
    ) -> str:
        """
        Export tasks data.
        
        Args:
            tasks: List of task dictionaries
            format: Export format
            **kwargs: Format-specific options
            
        Returns:
            Exported data string
        """
        if format == ExportFormat.JSON:
            return self.export_to_json(tasks, **kwargs)
        elif format == ExportFormat.CSV:
            return self.export_to_csv(tasks, **kwargs)
        elif format == ExportFormat.MARKDOWN:
            return self.export_to_markdown(tasks, title="Task Export", **kwargs)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def export_memories(
        self,
        memories: List[Dict],
        format: ExportFormat = ExportFormat.JSON,
        **kwargs
    ) -> str:
        """
        Export memory data.
        
        Args:
            memories: List of memory dictionaries
            format: Export format
            **kwargs: Format-specific options
            
        Returns:
            Exported data string
        """
        if format == ExportFormat.JSON:
            return self.export_to_json(memories, **kwargs)
        elif format == ExportFormat.CSV:
            return self.export_to_csv(memories, **kwargs)
        elif format == ExportFormat.MARKDOWN:
            return self.export_to_markdown(memories, title="Memory Export", **kwargs)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def export_analytics(
        self,
        analytics_data: Dict,
        format: ExportFormat = ExportFormat.JSON,
        **kwargs
    ) -> str:
        """
        Export analytics data.
        
        Args:
            analytics_data: Analytics dictionary
            format: Export format
            **kwargs: Format-specific options
            
        Returns:
            Exported data string
        """
        if format == ExportFormat.JSON:
            return self.export_to_json(analytics_data, **kwargs)
        elif format == ExportFormat.MARKDOWN:
            return self._export_analytics_markdown(analytics_data, **kwargs)
        else:
            raise ValueError(f"Unsupported format for analytics: {format}")
    
    def _export_analytics_markdown(self, data: Dict, **kwargs) -> str:
        """Export analytics as formatted Markdown report."""
        lines = [
            "# Analytics Report",
            f"\n*Generated: {datetime.now().isoformat()}*\n",
            "## Summary\n"
        ]
        
        # Summary metrics
        if 'summary' in data:
            for key, value in data['summary'].items():
                lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        
        # Performance metrics
        if 'performance' in data:
            lines.append("\n## Performance Metrics\n")
            for key, value in data['performance'].items():
                lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        
        # Usage statistics
        if 'usage' in data:
            lines.append("\n## Usage Statistics\n")
            for key, value in data['usage'].items():
                lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        
        markdown_str = "\n".join(lines)
        self._record_export(ExportFormat.MARKDOWN, "analytics_report")
        return markdown_str
    
    def create_export_package(
        self,
        tasks: Optional[List[Dict]] = None,
        memories: Optional[List[Dict]] = None,
        analytics: Optional[Dict] = None,
        format: ExportFormat = ExportFormat.JSON
    ) -> Dict[str, str]:
        """
        Create a complete export package with all data.
        
        Args:
            tasks: Task data
            memories: Memory data
            analytics: Analytics data
            format: Export format
            
        Returns:
            Dictionary with exported data for each category
        """
        package = {}
        
        if tasks:
            package['tasks'] = self.export_tasks(tasks, format)
        
        if memories:
            package['memories'] = self.export_memories(memories, format)
        
        if analytics:
            package['analytics'] = self.export_analytics(analytics, format)
        
        package['metadata'] = self.export_to_json({
            'export_date': datetime.now().isoformat(),
            'format': format,
            'included_data': list(package.keys())
        })
        
        logger.info(f"Created export package with {len(package)} items")
        return package
    
    def _record_export(self, format: ExportFormat, filename: Optional[str] = None):
        """Record export in history."""
        self.export_history.append({
            'timestamp': datetime.now().isoformat(),
            'format': format,
            'filename': filename
        })
    
    def get_export_history(self, limit: int = 100) -> List[Dict]:
        """
        Get export history.
        
        Args:
            limit: Maximum number of records
            
        Returns:
            List of export records
        """
        return self.export_history[-limit:]
    
    def clear_history(self):
        """Clear export history."""
        self.export_history = []
        logger.info("Export history cleared")


# Global export service instance
export_service = ExportService()