from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.utils.query_params_util import parse_optional_string, parse_optional_int

class PaginationParamsLogActivity(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Rows per page")
    search: str = Field('', description="Keyword search")
    sort: str = Field('', description="Sort format: column,direction (e.g., name,asc)")
    filter: int = Field(0, ge=0, description="Filter berdasarkan berapa hari terakhir (satuan hari)")


class PaginationParamsMasterData(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Rows per page")
    search: Optional[str] = Field('', description="Keyword search")
    sort: Optional[str] = Field('', description="Sort format: column,direction (e.g., name,asc)")
    kabkot: Optional[str] = Field('', description="Filter by kota/kabupaten")
    start_date_filter: Optional[str] = Field(None, ge=0, description="Filter berdasarkan start date")
    end_date_filter: Optional[str] = Field(None, ge=0, description="Filter berdasarkan end date")

class PaginationParamsMasterData(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Rows per page")
    search: Optional[str] = Field('', description="Keyword search")
    sort: Optional[str] = Field('', description="Sort format: column,direction (e.g., name,asc)")
    kabkot: Optional[str] = Field('', description="Filter by kota/kabupaten")
    start_date_filter: Optional[str] = Field(None, description="Filter berdasarkan start date")
    end_date_filter: Optional[str] = Field(None, description="Filter berdasarkan end date")


class PaginationParamsTrenKondisiJalan(BaseModel):

    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Rows per page")
    
    search: Optional[str] = Field(
        default=None, 
        description="Search keyword untuk kota, ruas_jalan, uptd, sup"
    )
    tanggal_mulai: Optional[str] = Field(
        default=None, 
        description="Filter tanggal mulai (format: MM/YYYY)"
    )
    tanggal_akhir: Optional[str] = Field(
        default=None, 
        description="Filter tanggal akhir (format: MM/YYYY)"
    )
    
    # Field existing
    nama_kota: Optional[str] = Field(
        default=None, 
        description="Filter by nama kota"
    )
    tahun: Optional[str] = Field(
        default=None, 
        description="Filter by tahun (contoh: 2025)"
    )

    @field_validator('nama_kota', 'search', mode='before')
    @classmethod
    def validate_optional_strings(cls, v):
        """Validate multiple optional string fields"""
        return parse_optional_string(v)

    @field_validator('tahun', mode='before')
    @classmethod
    def validate_tahun(cls, v):
        return v if v else None

    @property
    def tahun_int(self) -> Optional[int]:
        """Convert tahun string to integer"""
        return parse_optional_int(self.tahun)

class PaginationResponse(BaseModel):
    total: int = 0
    count: int = 0
    page: int = 0
    limit: int = 0
