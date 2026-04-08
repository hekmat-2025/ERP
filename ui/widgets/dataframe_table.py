from __future__ import annotations

import pandas as pd
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem


def fill_table_from_dataframe(table: QTableWidget, df: pd.DataFrame) -> None:
    table.setSortingEnabled(False)
    table.clear()

    if df is None or df.empty:
        table.setRowCount(0)
        table.setColumnCount(0)
        return

    df2 = df.copy()
    table.setColumnCount(len(df2.columns))
    table.setHorizontalHeaderLabels([str(c) for c in df2.columns])
    table.setRowCount(len(df2))

    for r in range(len(df2)):
        for c, col in enumerate(df2.columns):
            v = df2.iloc[r, c]
            item = QTableWidgetItem("" if v is None else str(v))
            table.setItem(r, c, item)

    table.resizeColumnsToContents()
    table.setSortingEnabled(True)

