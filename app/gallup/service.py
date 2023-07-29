from app.config import database

from .repository.repository import ShanyrakRepository
from .adapters.s3_service import S3Service
from .repository.comments_repository import CommentRepository
from .adapters.OpenAI_service import OpenAIService

class Service:
    def __init__(self):
        self.repository = ShanyrakRepository(database)
        self.comment_repository = CommentRepository(database)
        self.s3_service = S3Service()
        self.OpenAI_service = OpenAIService()


def get_service():
    return Service()
