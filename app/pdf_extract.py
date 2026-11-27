"""Run PDF parsing in a disposable child with only bounded stdin and stdout."""
import io
import json
import sys

from pypdf import PdfReader, apply_configuration


def main() -> int:
    max_pages, max_chars, max_bytes = map(int, sys.argv[1:])
    try:
        data = sys.stdin.buffer.read(max_bytes + 1)
        if len(data) > max_bytes:
            return 1
        with apply_configuration(
            maximum_declared_stream_length=2_000_000,
            zlib_maximum_output_length=2_000_000,
            lzw_maximum_output_length=2_000_000,
            run_length_maximum_output_length=2_000_000,
            stream_decoding_work_maximum_length=8_000_000,
            page_tree_maximum_entries=max_pages * 4 + 64,
            page_tree_maximum_page_entries=max_pages * 40 + 64,
            xform_maximum_invocations_per_extraction=500,
        ):
            reader = PdfReader(io.BytesIO(data), strict=True)
            if reader.is_encrypted:
                return 2
            count = len(reader.pages)
            if not 1 <= count <= max_pages:
                return 3
            pages = []
            size = 0
            for position, page in enumerate(reader.pages, 1):
                text = (page.extract_text() or "").strip()
                size += len(text)
                if size > max_chars:
                    return 4
                if text:
                    pages.append((position, text))
        if not pages:
            return 5
        sys.stdout.write(json.dumps({"page_count": count, "pages": pages}, ensure_ascii=True))
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
