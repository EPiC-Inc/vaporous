from flask import Blueprint, redirect, request, url_for
from werkzeug.wrappers.response import Response
from werkzeug.exceptions import NotFound

from .file_manip import list_files, retrieve

api = Blueprint('api', __name__)

@api.get('/dir/')
@api.get('/dir/<path:base_directory>')
def get_files_in_directory(base_directory='') -> dict | tuple[dict, int]:
    #TODO - check if user has access
    return list_files(base_directory)

@api.get('/file/<path:filename>')
def retrieve_file(filename) -> Response:
    try:
        return retrieve(filename)
    except NotFound:
        raise FileNotFoundError

@api.errorhandler(FileNotFoundError)
def file_not_found(e):
    return {}, 404