import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "benchmarks/eb006-research-completion-009"


def main():
    source = TASK / "data/observations.csv"
    target = TASK / "data/assay_observations.csv"
    with source.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    fields = ["candidate_id", "donor", "state", "condition", "assay", "adjusted_signal", "qc_status"]
    output = []
    for row in rows:
        for assay in ("A", "B"):
            value = row["adjusted_signal"]
            # Bounded assay disagreement: only C17 late/D4 treatment flips direction.
            if assay == "B" and row["candidate_id"] == "C17" and row["state"] == "late" and row["donor"] == "D4" and row["condition"] == "treatment":
                value = "1.00"
            output.append({
                "candidate_id": row["candidate_id"], "donor": row["donor"],
                "state": row["state"], "condition": row["condition"],
                "assay": assay, "adjusted_signal": value, "qc_status": row["qc_status"],
            })
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)


if __name__ == "__main__":
    main()
