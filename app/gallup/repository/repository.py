from typing import Optional, List

from bson.objectid import ObjectId
from pymongo.database import Database
from pymongo.results import DeleteResult, UpdateResult
import logging


class ShanyrakRepository:
    def __init__(self, database: Database):
        self.database = database

    def get_all_pdfs(self, user_id: str) -> List[dict]:
        pdfs = self.database["pdf"].find({"user_id": ObjectId(user_id)})
        return list(pdfs)

    def delete_pdf_by_id(self, pdf_id: str, user_id: str) -> DeleteResult:
        return self.database["pdf"].delete_one(
            {"_id": ObjectId(pdf_id), "user_id": ObjectId(user_id)}
        )

    def create_pdf(self, user_id: str, payload: dict):
        payload["user_id"] = ObjectId(user_id)
        pdf = self.database["pdf"].insert_one(payload)
        return pdf.inserted_id

    def update_pdf_by_id(self, pdf_id: str, user_id: str, data: dict) -> UpdateResult:
        return self.database["pdf"].update_one(
            filter={"_id": ObjectId(pdf_id), "user_id": ObjectId(user_id)},
            update={
                "$set": data,
            },
        )

    def get_pdf_url(self, pdf_id: str, user_id: str) -> Optional[dict]:
        user = self.database["pdf"].find_one(
            {"_id": ObjectId(pdf_id), "user_id": ObjectId(user_id)}
        )
        return user
