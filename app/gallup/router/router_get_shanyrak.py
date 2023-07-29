from typing import Any, List

from fastapi import Depends, Response
from pydantic import Field

from app.auth.adapters.jwt_service import JWTData
from app.auth.router.dependencies import parse_jwt_user_data
from app.utils import AppModel

from ..service import Service, get_service
from . import router
import logging


class GetPdfResponse(AppModel):
    id: Any = Field(alias="_id")
    date_of_test: str
    list_of_professions: str
    user_id: Any = Field(alias="user_id")
    pdf: str = ""
    pdf_similarities: str = ""
    pdf_comment: str = ""


@router.get("/all", response_model=List[GetPdfResponse])
def get_all_pdfs(
    jwt_data: JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
) -> List[GetPdfResponse]:
    pdfs = svc.repository.get_all_pdfs(user_id=jwt_data.user_id)
    logging.info(pdfs)
    return [GetPdfResponse(**pdf) for pdf in pdfs]


@router.get("/{pdf_id:str}/pdf_similarities_download")
def get_pdf_similarities(
    pdf_id: str,
    jwt_data: JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
) -> str:
    pdf_url = svc.repository.get_pdf_url(pdf_id=pdf_id, user_id=jwt_data.user_id)
    pdf_url = pdf_url.get("pdf_similarities")
    return pdf_url


@router.get("/{pdf_id:str}/pdf_comments_download")
def get_pdf_similarities(
    pdf_id: str,
    jwt_data: JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
) -> str:
    pdf_url = svc.repository.get_pdf_url(pdf_id=pdf_id, user_id=jwt_data.user_id)
    pdf_url = pdf_url.get("pdf_comment")
    return pdf_url
