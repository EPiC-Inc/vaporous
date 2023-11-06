from flask import (Blueprint, redirect, render_template, request, session,
                   url_for)
from werkzeug.wrappers.response import Response

from .file_manip import list_files, retrieve

composer = Blueprint('composer', __name__)

@composer.get('/dir_view/')
@composer.get('/dir_view/<path:base_directory>')
def compose_file_list(base_directory='') -> str | Response:
    #TODO - check if user has access
    # if not session.get("logged_in"):
    #     return redirect(url_for('index'))
    viewable_files = list_files(base_directory)
    return render_template('_file_list.html', files=viewable_files)