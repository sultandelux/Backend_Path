from fastapi import Depends, HTTPException, Response

from app.auth.adapters.jwt_service import JWTData
from app.auth.router.dependencies import parse_jwt_user_data

from ..service import Service, get_service
from . import router
from ...utils import AppModel
import logging



class CreateCommentRequest(AppModel):
    content: str


@router.post("/{id:str}/comments")
def create_comment(
    id: str,
    request: CreateCommentRequest,
    jwt_data: JWTData = Depends(parse_jwt_user_data),
    svc: Service = Depends(get_service),
) -> Response:
    user_id = jwt_data.user_id
    success = svc.comment_repository.create_comment(
        shanyrak_id=id, user_id=user_id, payload=request.dict()
    )
    df = pd.read_csv('s3://bucket-name/file.csv')
    logging.info(df)
    if not success:
        raise HTTPException(status_code=404, detail=f"Could not insert")
    return Response(status_code=200)
