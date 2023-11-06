from flask import (Blueprint, redirect, render_template, request, session,
                   url_for)


api = Blueprint('api', __name__)