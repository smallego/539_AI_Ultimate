from openpyxl.chart import BarChart, LineChart, Reference


def add_bar_chart(ws, title, start_row, data_col=2, label_col=1, position_col="E"):
    chart = BarChart()

    data = Reference(
        ws,
        min_col=data_col,
        min_row=start_row + 1,
        max_row=start_row + 10,
    )
    labels = Reference(
        ws,
        min_col=label_col,
        min_row=start_row + 2,
        max_row=start_row + 11,
    )

    chart.add_data(data, titles_from_data=True)
    chart.set_categories(labels)
    chart.title = title
    chart.width = 12
    chart.height = 6

    ws.add_chart(chart, f"{position_col}{start_row}")


def add_line_chart(ws, title, min_col, max_col, min_row, max_row, position, y_axis_title="Value"):
    chart = LineChart()
    chart.title = title
    chart.y_axis.title = y_axis_title
    chart.x_axis.title = "Draw"

    data = Reference(ws, min_col=min_col, max_col=max_col, min_row=min_row, max_row=max_row)
    chart.add_data(data, titles_from_data=True)

    chart.width = 18
    chart.height = 8
    ws.add_chart(chart, position)
