"""
Data Analysis Tool - Data Processing & Visualization
Provides CSV/Excel analysis, statistics, and visualization
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from app.tools.base_tool import BaseTool
from app.schemas.tool_schema import ToolInput, ToolResult, ToolCapability
from app.utils.logger import get_logger

logger = get_logger("tools.data_analysis")


class DataAnalysisTool(BaseTool):
    """
    Data processing and analysis
    
    Supported actions:
    - load: Load CSV/Excel file
    - describe: Get statistical summary
    - filter: Filter data by conditions
    - aggregate: Group and aggregate data
    - plot: Create visualization
    - export: Export processed data
    """
    
    def __init__(self, data_dir: str = "data/analysis"):
        super().__init__(
            name="data_analysis_tool",
            description="Analyze CSV/Excel data with statistics and visualization"
        )
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if pandas is available
        try:
            import pandas as pd
            self.pd = pd
            self.has_pandas = True
        except ImportError:
            self.logger.warning("Pandas not installed, functionality limited")
            self.pd = None
            self.has_pandas = False
        
        # Loaded datasets (in-memory cache)
        self.datasets: Dict[str, Any] = {}
    
    def execute(self, tool_input: ToolInput) -> ToolResult:
        """Execute data analysis action"""
        if not self.has_pandas:
            return ToolResult(
                success=False,
                error="Pandas not installed. Run: pip install pandas",
                error_type="internal_error"
            )
        
        action = tool_input.action.lower()
        params = tool_input.params
        
        action_map = {
            "load": self._load_data,
            "describe": self._describe_data,
            "filter": self._filter_data,
            "aggregate": self._aggregate_data,
            "plot": self._plot_data,
            "export": self._export_data
        }
        
        handler = action_map.get(action)
        if not handler:
            return ToolResult(
                success=False,
                error=f"Unknown action: {action}",
                error_type="validation"
            )
        
        return handler(params)
    
    def _load_data(self, params: Dict[str, Any]) -> ToolResult:
        """
        Load CSV or Excel file
        
        Params:
            path: File path
            format: File format (csv/excel) - auto-detected from extension
            dataset_id: ID to store dataset (optional)
        """
        path = params.get("path")
        format_type = params.get("format", "auto")
        dataset_id = params.get("dataset_id", "default")
        
        if not path:
            return ToolResult(
                success=False,
                error="path required",
                error_type="validation"
            )
        
        try:
            file_path = self.data_dir / path
            
            if not file_path.exists():
                return ToolResult(
                    success=False,
                    error=f"File not found: {path}",
                    error_type="resource_not_found"
                )
            
            # Auto-detect format
            if format_type == "auto":
                extension = file_path.suffix.lower()
                if extension == ".csv":
                    format_type = "csv"
                elif extension in [".xlsx", ".xls"]:
                    format_type = "excel"
                else:
                    return ToolResult(
                        success=False,
                        error=f"Unsupported file format: {extension}",
                        error_type="validation"
                    )
            
            # Load data
            if format_type == "csv":
                df = self.pd.read_csv(file_path)
            elif format_type == "excel":
                df = self.pd.read_excel(file_path)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown format: {format_type}",
                    error_type="validation"
                )
            
            # Store dataset
            self.datasets[dataset_id] = df
            
            return ToolResult(
                success=True,
                data={
                    "dataset_id": dataset_id,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": df.columns.tolist(),
                    "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                    "sample": df.head(5).to_dict('records')
                }
            )
            
        except Exception as e:
            self.logger.error(f"Load data failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="internal_error"
            )
    
    def _describe_data(self, params: Dict[str, Any]) -> ToolResult:
        """
        Get statistical summary
        
        Params:
            dataset_id: Dataset ID (default: 'default')
            columns: Specific columns to analyze (optional)
        """
        dataset_id = params.get("dataset_id", "default")
        columns = params.get("columns")
        
        if dataset_id not in self.datasets:
            return ToolResult(
                success=False,
                error=f"Dataset '{dataset_id}' not loaded",
                error_type="validation"
            )
        
        try:
            df = self.datasets[dataset_id]
            
            # Select columns if specified
            if columns:
                df = df[columns]
            
            # Get statistics
            description = df.describe(include='all').to_dict()
            
            # Get data types
            dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
            
            # Get null counts
            null_counts = df.isnull().sum().to_dict()
            
            # Get unique counts
            unique_counts = {col: int(df[col].nunique()) for col in df.columns}
            
            return ToolResult(
                success=True,
                data={
                    "dataset_id": dataset_id,
                    "statistics": description,
                    "dtypes": dtypes,
                    "null_counts": null_counts,
                    "unique_counts": unique_counts,
                    "total_rows": len(df),
                    "total_columns": len(df.columns)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Describe data failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="internal_error"
            )
    
    def _filter_data(self, params: Dict[str, Any]) -> ToolResult:
        """
        Filter data by conditions
        
        Params:
            dataset_id: Dataset ID
            conditions: Filter conditions (dict)
            save_as: Save filtered data as new dataset ID (optional)
        """
        dataset_id = params.get("dataset_id", "default")
        conditions = params.get("conditions", {})
        save_as = params.get("save_as")
        
        if dataset_id not in self.datasets:
            return ToolResult(
                success=False,
                error=f"Dataset '{dataset_id}' not loaded",
                error_type="validation"
            )
        
        try:
            df = self.datasets[dataset_id].copy()
            
            # Apply filters
            for column, condition in conditions.items():
                if column not in df.columns:
                    return ToolResult(
                        success=False,
                        error=f"Column '{column}' not found",
                        error_type="validation"
                    )
                
                # Simple equality filter
                if isinstance(condition, (str, int, float)):
                    df = df[df[column] == condition]
                # Range filter
                elif isinstance(condition, dict):
                    if 'min' in condition:
                        df = df[df[column] >= condition['min']]
                    if 'max' in condition:
                        df = df[df[column] <= condition['max']]
            
            # Save as new dataset if requested
            if save_as:
                self.datasets[save_as] = df
            
            return ToolResult(
                success=True,
                data={
                    "dataset_id": save_as or dataset_id,
                    "rows_before": len(self.datasets[dataset_id]),
                    "rows_after": len(df),
                    "rows_removed": len(self.datasets[dataset_id]) - len(df),
                    "sample": df.head(5).to_dict('records')
                }
            )
            
        except Exception as e:
            self.logger.error(f"Filter data failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="internal_error"
            )
    
    def _aggregate_data(self, params: Dict[str, Any]) -> ToolResult:
        """
        Group and aggregate data
        
        Params:
            dataset_id: Dataset ID
            group_by: Column(s) to group by
            aggregations: Aggregations to perform {column: function}
        """
        dataset_id = params.get("dataset_id", "default")
        group_by = params.get("group_by")
        aggregations = params.get("aggregations", {})
        
        if dataset_id not in self.datasets:
            return ToolResult(
                success=False,
                error=f"Dataset '{dataset_id}' not loaded",
                error_type="validation"
            )
        
        if not group_by:
            return ToolResult(
                success=False,
                error="group_by required",
                error_type="validation"
            )
        
        try:
            df = self.datasets[dataset_id]
            
            # Perform aggregation
            grouped = df.groupby(group_by).agg(aggregations)
            
            # Convert to records
            result = grouped.reset_index().to_dict('records')
            
            return ToolResult(
                success=True,
                data={
                    "dataset_id": dataset_id,
                    "group_by": group_by,
                    "aggregations": aggregations,
                    "groups": len(result),
                    "result": result
                }
            )
            
        except Exception as e:
            self.logger.error(f"Aggregate data failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="internal_error"
            )
    
    def _plot_data(self, params: Dict[str, Any]) -> ToolResult:
        """
        Create visualization
        
        Params:
            dataset_id: Dataset ID
            plot_type: Type of plot (line/bar/scatter/hist)
            x: X-axis column
            y: Y-axis column
            output_path: Path to save plot (optional)
        """
        # Placeholder - requires matplotlib
        return ToolResult(
            success=False,
            error="Plotting not yet implemented (requires matplotlib)",
            error_type="internal_error"
        )
    
    def _export_data(self, params: Dict[str, Any]) -> ToolResult:
        """
        Export processed data
        
        Params:
            dataset_id: Dataset ID
            output_path: Output file path
            format: Output format (csv/excel/json)
        """
        dataset_id = params.get("dataset_id", "default")
        output_path = params.get("output_path")
        format_type = params.get("format", "csv")
        
        if dataset_id not in self.datasets:
            return ToolResult(
                success=False,
                error=f"Dataset '{dataset_id}' not loaded",
                error_type="validation"
            )
        
        if not output_path:
            return ToolResult(
                success=False,
                error="output_path required",
                error_type="validation"
            )
        
        try:
            df = self.datasets[dataset_id]
            output_file = self.data_dir / output_path
            
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format_type == "csv":
                df.to_csv(output_file, index=False)
            elif format_type == "excel":
                df.to_excel(output_file, index=False)
            elif format_type == "json":
                df.to_json(output_file, orient='records', indent=2)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown format: {format_type}",
                    error_type="validation"
                )
            
            return ToolResult(
                success=True,
                data={
                    "dataset_id": dataset_id,
                    "output_path": str(output_file),
                    "format": format_type,
                    "rows": len(df),
                    "columns": len(df.columns)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Export data failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="internal_error"
            )
    
    def get_capability(self) -> ToolCapability:
        """Get data analysis capability"""
        return ToolCapability(
            name=self.name,
            description=self.description,
            supported_actions=[
                "load", "describe", "filter",
                "aggregate", "plot", "export"
            ],
            required_params={
                "load": "path",
                "describe": "",
                "filter": "conditions",
                "aggregate": "group_by, aggregations",
                "export": "output_path"
            },
            optional_params={
                "load": "format, dataset_id",
                "describe": "dataset_id, columns",
                "filter": "dataset_id, save_as",
                "aggregate": "dataset_id",
                "export": "dataset_id, format"
            },
            requires_auth=False,
            examples=[
                {
                    "action": "load",
                    "params": {"path": "sales.csv"},
                    "description": "Load CSV file"
                },
                {
                    "action": "describe",
                    "params": {"dataset_id": "default"},
                    "description": "Get statistical summary"
                },
                {
                    "action": "filter",
                    "params": {
                        "dataset_id": "default",
                        "conditions": {"region": "North", "sales": {"min": 1000}}
                    },
                    "description": "Filter by region and minimum sales"
                }
            ]
        )
    
    def health_check(self) -> bool:
        """Check if pandas is available"""
        return self.has_pandas


if __name__ == "__main__":
    """Test data analysis tool"""
    print("📊 Testing Data Analysis Tool...")
    
    # Check if pandas is available
    try:
        import pandas as pd
        
        analysis_tool = DataAnalysisTool()
        
        # Create sample data
        sample_data = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie', 'David'],
            'age': [25, 30, 35, 28],
            'sales': [1000, 1500, 1200, 1800]
        })
        
        # Save sample CSV
        sample_path = Path("data/analysis/sample.csv")
        sample_path.parent.mkdir(parents=True, exist_ok=True)
        sample_data.to_csv(sample_path, index=False)
        
        # Test load
        print("\n📥 Testing load...")
        result = analysis_tool.run(ToolInput(
            action="load",
            params={"path": "sample.csv"}
        ))
        print(f"   Success: {result.success}")
        print(f"   Rows: {result.data.get('rows', 0)}")
        print(f"   Columns: {result.data.get('columns', 0)}")
        
        # Test describe
        print("\n📈 Testing describe...")
        result = analysis_tool.run(ToolInput(
            action="describe",
            params={"dataset_id": "default"}
        ))
        print(f"   Success: {result.success}")
        
        # Test filter
        print("\n🔍 Testing filter...")
        result = analysis_tool.run(ToolInput(
            action="filter",
            params={
                "dataset_id": "default",
                "conditions": {"sales": {"min": 1200}}
            }
        ))
        print(f"   Success: {result.success}")
        print(f"   Rows after filter: {result.data.get('rows_after', 0)}")
        
        print("\n✅ Data analysis tool test complete")
        
    except ImportError:
        print("\n⚠️ Pandas not installed - skipping tests")
        print("   Install with: pip install pandas")