from flask import Blueprint

main = Blueprint('main', __name__)

from . import routes, categories, products, print_jobs, users, analytics 

