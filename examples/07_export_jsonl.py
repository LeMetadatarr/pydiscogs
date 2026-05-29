"""Export a small JSONL sample of one dataset config."""
import pydiscogs


def main() -> None:
    out = "discogs_labels_sample.jsonl"
    n = pydiscogs.export_jsonl("labels", out, limit=500)
    print(f"wrote {n} records to {out}")


if __name__ == "__main__":
    main()
