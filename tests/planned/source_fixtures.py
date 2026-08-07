from __future__ import annotations

import fitz


def pdf_bytes(text: str) -> bytes:
    return pdf_bytes_pages([text])


def pdf_bytes_pages(page_texts: list[str]) -> bytes:
    document = fitz.open()
    for text in page_texts:
        page = document.new_page()
        page.insert_textbox(fitz.Rect(54, 54, 540, 760), text, fontsize=11)
    payload = document.tobytes(garbage=4, deflate=True)
    document.close()
    return payload


def upload_pdf(client, workspace_id: str, name: str, text: str, authority: str = "normative"):
    return upload_pdf_pages(client, workspace_id, name, [text], authority)


def upload_pdf_pages(
    client,
    workspace_id: str,
    name: str,
    page_texts: list[str],
    authority: str = "normative",
):
    return client.post(
        f"/api/workspaces/{workspace_id}/sources",
        data={"authority": authority},
        files={"file": (name, pdf_bytes_pages(page_texts), "application/pdf")},
    )
