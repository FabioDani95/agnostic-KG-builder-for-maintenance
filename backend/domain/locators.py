"""Format-independent discriminated source locator union."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PdfLocator(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["pdf"] = "pdf"
    page: int = Field(ge=1)
    section: str | None = None
    quote: str = Field(min_length=1)
    extraction_method: Literal["native_text", "table", "ocr"]
    printed_page: str | None = None
    block_index: int | None = Field(default=None, ge=0)
    source_block_index: int | None = Field(default=None, ge=0)
    bbox: tuple[float, float, float, float] | None = None
    table_index: int | None = Field(default=None, ge=1)
    row_index: int | None = Field(default=None, ge=1)
    ocr_region_index: int | None = Field(default=None, ge=1)


class TableRowLocator(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["table_row"] = "table_row"
    table_id: str
    table_name: str
    record: int = Field(ge=1)
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    columns: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def ordered_lines(self) -> "TableRowLocator":
        if self.line_end < self.line_start:
            raise ValueError("line_end must not precede line_start")
        return self


class XlsxRowLocator(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["xlsx_row"] = "xlsx_row"
    sheet: str
    row: int = Field(ge=1)
    cells: list[str] = Field(default_factory=list)


class JsonPathLocator(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["json_path"] = "json_path"
    json_path: str
    line: int | None = Field(default=None, ge=1)


class OperatorInputLocator(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["operator_input"] = "operator_input"
    assertion_id: str
    decision_id: str
    field_path: str


SourceLocator = Annotated[
    PdfLocator | TableRowLocator | XlsxRowLocator | JsonPathLocator | OperatorInputLocator,
    Field(discriminator="kind"),
]
