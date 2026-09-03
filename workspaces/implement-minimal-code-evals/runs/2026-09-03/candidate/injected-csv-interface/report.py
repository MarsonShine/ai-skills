import csv
from abc import ABC, abstractmethod
from io import StringIO


class ReportSink(ABC):
    @abstractmethod
    def write(self, text):
        """Receive CSV text."""
        raise NotImplementedError


class CsvBuffer(ReportSink):
    def __init__(self):
        self.parts = []

    def write(self, text):
        self.parts.append(text)

    def getvalue(self):
        return "".join(self.parts)


def export_totals(rows, sink: ReportSink):
    totals = {}
    for row in rows:
        category = row["category"]
        totals[category] = totals.get(category, 0) + row["amount_cents"]

    with StringIO(newline="") as report:
        writer = csv.writer(report)
        writer.writerow(("category", "total_cents"))
        writer.writerows(
            (category, totals[category]) for category in sorted(totals)
        )
        sink.write(report.getvalue())

    return len(totals)
