"""Cache the smallest dump on disk, then stream it offline.

The first call downloads the whole labels dump into PYDISCOGS_CACHE
(~/.cache/pydiscogs by default); subsequent runs reuse it. Streaming from the
local file uses the same memory-safe parser and makes no network call.
"""
import pydiscogs


def main() -> None:
    path = pydiscogs.download("labels")
    print("cached at", path)

    for label in pydiscogs.stream("labels", local=path, limit=5):
        print(label.id, label.name)


if __name__ == "__main__":
    main()
