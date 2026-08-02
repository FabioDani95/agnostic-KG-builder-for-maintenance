from __future__ import annotations

import fitz


def pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_textbox(fitz.Rect(54, 54, 540, 760), text, fontsize=11)
    payload = document.tobytes(garbage=4, deflate=True)
    document.close()
    return payload


def upload_pdf(client, workspace_id: str, name: str, text: str, authority: str = "normative"):
    return client.post(
        f"/api/workspaces/{workspace_id}/sources",
        data={"authority": authority},
        files={"file": (name, pdf_bytes(text), "application/pdf")},
    )

