from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from flask_paginate import Pagination, get_page_parameter
from sqlalchemy import desc
from decimal import Decimal

from app.models import PrintJob
from .decorators import store_admin_required

from . import main

# Constants for pagination
PER_PAGE = 10

@main.route('/print_jobs')
@login_required
def print_jobs():
    """
    View function for listing print jobs.
    Store admins see all print jobs, staff see only their own.
    Shows detailed information using relationships.
    """
    try:
        success_message = request.args.get('success_message')
        page = request.args.get(get_page_parameter(), type=int, default=1)
        
        # Filter query based on user role
        query = PrintJob.query
        if current_user.role != 'store_admin':
            query = query.filter_by(user_id=current_user.id)
        
        # Order by print date, most recent first
        print_jobs_pagination = query.order_by(
            desc(PrintJob.print_date)
        ).paginate(
            page=page,
            per_page=PER_PAGE,
            error_out=False
        )

        # Calculate values for each print job
        jobs_with_values = []
        for job in print_jobs_pagination.items:
            value = Decimal('0.00')
            if job.product:
                value = job.quantity * job.product.rate
            
            jobs_with_values.append({
                'job': job,
                'value': value
            })
        
        return render_template(
            'print_jobs.html',
            print_jobs=jobs_with_values,
            pagination=Pagination(
                page=page,
                total=print_jobs_pagination.total,
                search=False,
                per_page=PER_PAGE,
                css_framework='bootstrap4'
            ),
            success_message=success_message,
            is_admin=current_user.role == 'store_admin'
        )
    except Exception as e:
        flash(f'Error loading print jobs: {str(e)}', 'danger')
        return redirect(url_for('main.index'))
