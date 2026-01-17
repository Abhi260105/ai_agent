"""
UI Schema Models - Data models for UI components
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ThemeMode(str, Enum):
    """UI theme modes."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class ViewMode(str, Enum):
    """View display modes."""
    CARDS = "cards"
    TABLE = "table"
    LIST = "list"
    GRID = "grid"


class DashboardData(BaseModel):
    """Data model for dashboard display."""
    summary_stats: Dict[str, Any] = Field(default_factory=dict)
    recent_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    active_tools: List[Dict[str, Any]] = Field(default_factory=list)
    memory_stats: Dict[str, Any] = Field(default_factory=dict)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)


class ProgressUpdate(BaseModel):
    """Progress update model for real-time updates."""
    task_id: str
    progress: int = Field(ge=0, le=100)
    status: str
    current_step: str
    steps_completed: int
    total_steps: int
    elapsed_time: float
    estimated_remaining: Optional[float] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class UserPreferences(BaseModel):
    """User preferences for UI customization."""
    theme: ThemeMode = Field(default=ThemeMode.LIGHT)
    default_view_mode: ViewMode = Field(default=ViewMode.CARDS)
    items_per_page: int = Field(default=10, ge=5, le=100)
    enable_notifications: bool = Field(default=True)
    enable_sound: bool = Field(default=False)
    auto_refresh: bool = Field(default=True)
    refresh_interval: int = Field(default=30, ge=5, le=300, description="Seconds")
    show_advanced_options: bool = Field(default=False)
    compact_mode: bool = Field(default=False)
    language: str = Field(default="en")
    timezone: str = Field(default="UTC")
    date_format: str = Field(default="YYYY-MM-DD")
    time_format: str = Field(default="24h")


class ExportFormat(str, Enum):
    """Export format options."""
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    PDF = "pdf"
    HTML = "html"


class ExportOptions(BaseModel):
    """Options for data export."""
    format: ExportFormat
    include_metadata: bool = Field(default=True)
    include_timestamps: bool = Field(default=True)
    pretty_print: bool = Field(default=True)
    compress: bool = Field(default=False)
    filters: Dict[str, Any] = Field(default_factory=dict)
    columns: Optional[List[str]] = None


class FilterOptions(BaseModel):
    """Filter options for data views."""
    search_query: Optional[str] = None
    status_filter: Optional[List[str]] = None
    priority_filter: Optional[List[str]] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    tags: Optional[List[str]] = None
    custom_filters: Dict[str, Any] = Field(default_factory=dict)


class SortOptions(BaseModel):
    """Sort options for data views."""
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
    secondary_sort: Optional[str] = None


class ChartData(BaseModel):
    """Data model for chart visualization."""
    chart_type: str = Field(description="bar, line, pie, scatter, etc.")
    title: str
    labels: List[str]
    datasets: List[Dict[str, Any]]
    options: Dict[str, Any] = Field(default_factory=dict)


class TableColumn(BaseModel):
    """Table column configuration."""
    key: str
    label: str
    width: Optional[int] = None
    sortable: bool = Field(default=True)
    filterable: bool = Field(default=True)
    format: Optional[str] = None
    align: str = Field(default="left", pattern="^(left|center|right)$")


class TableConfig(BaseModel):
    """Table configuration."""
    columns: List[TableColumn]
    default_sort: Optional[str] = None
    page_size: int = Field(default=10)
    enable_selection: bool = Field(default=True)
    enable_pagination: bool = Field(default=True)
    enable_search: bool = Field(default=True)
    sticky_header: bool = Field(default=True)


class NotificationMessage(BaseModel):
    """UI notification message."""
    id: str
    type: str = Field(description="info, success, warning, error")
    title: str
    message: str
    duration: int = Field(default=5000, description="Duration in milliseconds")
    action: Optional[Dict[str, str]] = None
    dismissible: bool = Field(default=True)
    timestamp: datetime = Field(default_factory=datetime.now)


class ModalConfig(BaseModel):
    """Modal dialog configuration."""
    title: str
    content: str
    type: str = Field(default="info", description="info, confirm, alert")
    size: str = Field(default="medium", pattern="^(small|medium|large)$")
    buttons: List[Dict[str, Any]] = Field(default_factory=list)
    closable: bool = Field(default=True)


class FormField(BaseModel):
    """Form field configuration."""
    name: str
    label: str
    type: str = Field(description="text, number, select, checkbox, textarea, etc.")
    required: bool = Field(default=False)
    placeholder: Optional[str] = None
    default_value: Any = None
    validation: Optional[Dict[str, Any]] = None
    options: Optional[List[Dict[str, str]]] = None
    help_text: Optional[str] = None


class FormConfig(BaseModel):
    """Form configuration."""
    title: str
    fields: List[FormField]
    submit_text: str = Field(default="Submit")
    cancel_text: str = Field(default="Cancel")
    layout: str = Field(default="vertical", pattern="^(vertical|horizontal|grid)$")
    validation_mode: str = Field(default="onSubmit", pattern="^(onChange|onBlur|onSubmit)$")


class WidgetConfig(BaseModel):
    """Dashboard widget configuration."""
    id: str
    type: str = Field(description="chart, stat, list, table, etc.")
    title: str
    size: str = Field(default="medium", pattern="^(small|medium|large|full)$")
    position: Dict[str, int] = Field(default_factory=dict)
    refresh_interval: Optional[int] = None
    data_source: str
    config: Dict[str, Any] = Field(default_factory=dict)


class DashboardLayout(BaseModel):
    """Dashboard layout configuration."""
    widgets: List[WidgetConfig]
    columns: int = Field(default=3, ge=1, le=6)
    gap: int = Field(default=16, description="Gap in pixels")
    auto_arrange: bool = Field(default=True)


class NavigationItem(BaseModel):
    """Navigation menu item."""
    id: str
    label: str
    icon: Optional[str] = None
    path: str
    badge: Optional[str] = None
    children: Optional[List['NavigationItem']] = None
    visible: bool = Field(default=True)
    disabled: bool = Field(default=False)


class UIState(BaseModel):
    """Global UI state."""
    current_page: str
    sidebar_collapsed: bool = Field(default=False)
    modal_stack: List[ModalConfig] = Field(default_factory=list)
    notifications: List[NotificationMessage] = Field(default_factory=list)
    loading: bool = Field(default=False)
    selected_items: List[str] = Field(default_factory=list)
    filters: FilterOptions = Field(default_factory=FilterOptions)
    preferences: UserPreferences = Field(default_factory=UserPreferences)


# Recursive model reference
NavigationItem.model_rebuild()