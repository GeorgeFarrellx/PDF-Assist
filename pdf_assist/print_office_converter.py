from __future__ import annotations

from pathlib import Path

WORD_EXTENSIONS = {".doc", ".docx"}
EXCEL_EXTENSIONS = {".xls", ".xlsx", ".xlsm", ".xlsb"}
MSG_EXTENSIONS = {".msg"}


class OfficeConversionError(RuntimeError):
    pass


def _import_win32_modules():
    try:
        import pythoncom  # type: ignore
        import win32com.client  # type: ignore
    except Exception as exc:  # pragma: no cover - platform specific
        raise OfficeConversionError(
            "Microsoft Office/Outlook conversion requires Windows + pywin32 + the relevant Office application."
        ) from exc
    return pythoncom, win32com.client


def convert_word_to_pdf(source_path: str | Path, output_path: str | Path) -> Path:
    pythoncom, win32_client = _import_win32_modules()
    source = str(Path(source_path).resolve())
    output = str(Path(output_path).resolve())
    pythoncom.CoInitialize()
    word = None
    doc = None
    try:
        word = win32_client.DispatchEx("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(source, ReadOnly=True)
        doc.ExportAsFixedFormat(output, 17)
        return Path(output)
    except Exception as exc:  # pragma: no cover
        raise OfficeConversionError(f"Word conversion failed for '{source}': {exc}") from exc
    finally:
        if doc is not None:
            doc.Close(False)
        if word is not None:
            word.Quit()
        pythoncom.CoUninitialize()


def convert_excel_to_pdf(source_path: str | Path, output_path: str | Path) -> Path:
    pythoncom, win32_client = _import_win32_modules()
    source = str(Path(source_path).resolve())
    output = str(Path(output_path).resolve())
    pythoncom.CoInitialize()
    excel = None
    wb = None
    try:
        excel = win32_client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        wb = excel.Workbooks.Open(source, ReadOnly=True)
        wb.ExportAsFixedFormat(0, output)
        return Path(output)
    except Exception as exc:  # pragma: no cover
        raise OfficeConversionError(f"Excel conversion failed for '{source}': {exc}") from exc
    finally:
        if wb is not None:
            wb.Close(False)
        if excel is not None:
            excel.Quit()
        pythoncom.CoUninitialize()


def convert_msg_to_pdf(source_path: str | Path, output_path: str | Path) -> Path:
    pythoncom, win32_client = _import_win32_modules()
    source = str(Path(source_path).resolve())
    output = str(Path(output_path).resolve())
    temp_html = str(Path(output).with_suffix(".html"))
    pythoncom.CoInitialize()
    outlook = None
    mail_item = None
    word = None
    html_doc = None
    try:
        outlook = win32_client.DispatchEx("Outlook.Application")
        mail_item = outlook.Session.OpenSharedItem(source)
        html_body = mail_item.HTMLBody or mail_item.Body or ""
        Path(temp_html).write_text(html_body, encoding="utf-8", errors="ignore")

        word = win32_client.DispatchEx("Word.Application")
        word.Visible = False
        html_doc = word.Documents.Open(temp_html, ReadOnly=True)
        html_doc.ExportAsFixedFormat(output, 17)
        return Path(output)
    except Exception as exc:  # pragma: no cover
        raise OfficeConversionError(f"MSG conversion failed for '{source}': {exc}") from exc
    finally:
        if html_doc is not None:
            html_doc.Close(False)
        if word is not None:
            word.Quit()
        if mail_item is not None:
            mail_item.Close(0)
        if outlook is not None:
            outlook.Quit()
        try:
            Path(temp_html).unlink(missing_ok=True)
        except Exception:
            pass
        pythoncom.CoUninitialize()


def convert_office_or_msg_to_pdf(source_path: str | Path, output_path: str | Path) -> Path:
    ext = Path(source_path).suffix.lower()
    if ext in WORD_EXTENSIONS:
        return convert_word_to_pdf(source_path, output_path)
    if ext in EXCEL_EXTENSIONS:
        return convert_excel_to_pdf(source_path, output_path)
    if ext in MSG_EXTENSIONS:
        return convert_msg_to_pdf(source_path, output_path)
    raise OfficeConversionError(f"Unsupported office conversion type: {ext}")
