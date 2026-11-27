"""Local Windows capacity probe. Real PDF, tokenizer and CPU model; no cloud writes."""
import ctypes
import io
import json
import sys
from pathlib import Path
from contextlib import contextmanager
from threading import BoundedSemaphore, Event, Thread
from time import perf_counter
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.embeddings import MiniLM
from app.config import OracleSettings
from app.library import Library, extract
from app.oracle import connect


def source(page_count, lines):
    writer = PdfWriter()
    for index in range(1, page_count + 1):
        page = writer.add_blank_page(width=595, height=842)
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): DictionaryObject({
                NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            })}),
        })
        rows = [
            f"Section {index}.{line}: The checkpoint records completed database restore operations "
            "before recovery commits. Compare the version counter and verify page integrity."
            for line in range(lines)
        ]
        stream = DecodedStreamObject()
        stream.set_data(("BT /F1 9 Tf 36 800 Td 14 TL " +
                         " T* ".join(f"({line}) Tj" for line in rows) + " ET").encode("ascii"))
        page[NameObject("/Contents")] = stream
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def windows_peak_mib():
    if sys.platform != "win32":
        return None

    class Counters(ctypes.Structure):
        _fields_ = [("size", ctypes.c_ulong), ("faults", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in (
                "peak", "working", "paged_peak", "paged", "nonpaged_peak",
                "nonpaged", "pagefile", "peak_pagefile",
            )
        ]

    counters = Counters()
    counters.size = ctypes.sizeof(counters)
    if not ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.c_void_p(-1), ctypes.byref(counters), counters.size):
        return None
    return round(counters.peak / 2**20, 1)


def measure(model, pages, lines, connection=None):
    lib = Library(SimpleNamespace(), "", model, BoundedSemaphore(1))
    lib.max_pages, lib.max_bytes, lib.max_chars, lib.max_chunks = 40, 5_000_000, 120_000, 128
    raw = source(pages, lines)
    conn, parsed, encoding = MagicMock(), {}, []
    conn.cursor.return_value.__enter__.return_value.fetchone.side_effect = [None, (0,)]
    complete = Event()
    probes = []
    io_times = []
    doc_id = None

    @contextmanager
    def rollback_writer():
        class NoCommit:
            def cursor(self):
                return connection.cursor()

            def commit(self):
                # The surrounding benchmark rolls back the entire fixture.
                pass

        start = perf_counter()
        try:
            yield NoCommit()
        finally:
            io_times.append((perf_counter() - start) * 1000)

    def poll_admission():
        while not complete.wait(.02):
            acquired = lib.admission.acquire(blocking=False)
            probes.append(acquired)
            if acquired:
                lib.admission.release()

    original_encode = model.encode

    def timed_extract(*args):
        start = perf_counter()
        result = extract(*args)
        parsed.update(parse_ms=(perf_counter() - start) * 1000,
                      characters=sum(len(text) for _, text in result[1]))
        return result

    def timed_encode(*args):
        start = perf_counter()
        result = original_encode(*args)
        encoding.append((len(result), (perf_counter() - start) * 1000))
        return result

    with patch.object(lib, "writer") as writer, patch("app.library.extract", timed_extract), \
            patch.object(model, "encode", timed_encode):
        if connection is None:
            writer.return_value.__enter__.return_value = conn
        else:
            writer.side_effect = rollback_writer
        thread = Thread(target=poll_admission)
        thread.start()
        start = perf_counter()
        try:
            doc_id, duplicate = lib.ingest(raw, "capacity.pdf", "pdf")
            status = "duplicate" if duplicate else "prepared"
        except ValueError as error:
            status = str(error)
        finally:
            complete.set()
            thread.join()
        elapsed = (perf_counter() - start) * 1000
    return dict(pages=pages, lines_per_page=lines, file_bytes=len(raw), **parsed, status=status,
                encoded_chunks=sum(n for n, _ in encoding), embedding_ms=sum(ms for _, ms in encoding),
                max_batch_ms=max((ms for _, ms in encoding), default=0), local_ms=elapsed,
                admission_probes=len(probes), busy_probes=probes.count(False), process_peak_mib=windows_peak_mib(),
                oracle_write_ms=io_times[1] if len(io_times) == 2 else None, document_id=doc_id)


if __name__ == "__main__":
    model = MiniLM()
    model.encode(["Warm the database embedding model."])
    print(json.dumps({"warm_process_peak_mib": windows_peak_mib()}), flush=True)
    if sys.argv[1:] == ["--oracle-rollback"]:
        with connect(OracleSettings.from_env()) as connection:
            assert not connection.autocommit
            for profile in ((20, 16), (40, 16)):
                result = None
                try:
                    result = measure(model, *profile, connection)
                    assert result["status"] == "prepared" and result["oracle_write_ms"] is not None
                finally:
                    connection.rollback()
                with connection.cursor() as cursor:
                    cursor.execute("SELECT count(*) FROM documents WHERE document_id=:id",
                                   id=result.pop("document_id"))
                    assert cursor.fetchone()[0] == 0
                print(json.dumps(result), flush=True)
    else:
        for profile in ((20, 16), (40, 16), (40, 10)):
            result = measure(model, *profile)
            result.pop("document_id")
            print(json.dumps(result), flush=True)
