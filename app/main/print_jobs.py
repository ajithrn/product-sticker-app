from flask import render_template, request
from flask_login import login_required
from flask_paginate import Pagination, get_page_parameter

from app.models import PrintJob

from . import main

# Constants for pagination
PER_PAGE = 10

@main.route('/print_jobs')
@login_required
def print_jobs():
    """
    View function for listing all print jobs.
    """
    success_message = request.args.get('success_message')
    page = request.args.get(get_page_parameter(), type=int, default=1)
    print_jobs_pagination = PrintJob.query.order_by(
        PrintJob.id.desc()
    ).paginate(
        page=page,
        per_page=PER_PAGE,
        error_out=False
    )
    print_jobs = print_jobs_pagination.items
    pagination = Pagination(
        page=page,
        total=print_jobs_pagination.total,
        search=False,
        per_page=PER_PAGE,
        css_framework='bootstrap4'
    )
    return render_template(
        'print_jobs.html',
        print_jobs=print_jobs,
        pagination=pagination,
        success_message=success_message
    )
