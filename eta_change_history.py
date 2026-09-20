import csv

class ETAChangeHistory:
    def __init__(self):
        self.records = []

    def add(self, record):
        if record is None:
            raise ValueError("History record cannot be None.")
        self.records.append(dict(record))

    def all(self):
        return list(self.records)

    def eta_changed_count(self):
        etas = [r.get("first_eta") for r in self.records]
        return sum(1 for i in range(1, len(etas)) if etas[i] != etas[i-1])

    def export_csv(self, path):
        if not self.records:
            raise ValueError("Cannot export empty history.")
        fields = list(self.records[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(self.records)
