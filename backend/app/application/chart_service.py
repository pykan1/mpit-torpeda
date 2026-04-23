from app.domain.entities import ChartType, QueryResult


def auto_select_chart(columns: list[str], rows: list[list], suggested: str | None = None) -> ChartType:
    """Auto-select chart type based on data shape and AI suggestion."""
    if suggested and suggested in ChartType.__members__.values():
        return ChartType(suggested)

    if not rows or not columns:
        return ChartType.TABLE

    num_cols = len(columns)
    num_rows = len(rows)

    # KPI: single value
    if num_cols == 1 and num_rows == 1:
        return ChartType.KPI

    # Time series detection
    time_keywords = ["date", "week", "month", "day", "hour", "time", "период", "дата"]
    has_time = any(kw in col.lower() for col in columns for kw in time_keywords)
    if has_time and num_cols >= 2:
        return ChartType.LINE

    # Category + metric = bar
    if num_cols == 2:
        return ChartType.BAR

    # Many cols = table
    if num_cols > 4:
        return ChartType.TABLE

    # Few rows, two cols = pie
    if num_rows <= 8 and num_cols == 2:
        return ChartType.PIE

    return ChartType.BAR


def build_chart_data(
    columns: list[str],
    rows: list[list],
    chart_type: ChartType,
    chart_config: dict | None = None,
) -> dict:
    """Build Chart.js compatible data structure."""
    if not rows or chart_type == ChartType.TABLE:
        return {}

    config = chart_config or {}
    x_col = config.get("x_column") or columns[0]
    y_col = config.get("y_column") or (columns[1] if len(columns) > 1 else columns[0])

    x_idx = columns.index(x_col) if x_col in columns else 0
    y_idx = columns.index(y_col) if y_col in columns else min(1, len(columns) - 1)

    labels = [str(row[x_idx]) for row in rows]
    values = []
    for row in rows:
        try:
            values.append(float(row[y_idx]))
        except (ValueError, TypeError):
            values.append(0)

    DRIVEE_COLORS = [
        "#2ECC71", "#27AE60", "#F39C12", "#E74C3C",
        "#3498DB", "#9B59B6", "#1ABC9C", "#E67E22",
        "#F1C40F", "#16A085",
    ]

    if chart_type == ChartType.KPI:
        return {
            "value": values[0] if values else 0,
            "label": y_col,
        }

    if chart_type in (ChartType.PIE, ChartType.DOUGHNUT):
        return {
            "labels": labels,
            "datasets": [{
                "data": values,
                "backgroundColor": DRIVEE_COLORS[:len(labels)],
                "borderColor": "#ffffff",
                "borderWidth": 2,
            }],
        }

    # Bar and Line
    return {
        "labels": labels,
        "datasets": [{
            "label": y_col.replace("_", " ").title(),
            "data": values,
            "backgroundColor": "#2ECC7180",
            "borderColor": "#27AE60",
            "borderWidth": 2,
            "fill": chart_type == ChartType.LINE,
            "tension": 0.4,
        }],
    }
