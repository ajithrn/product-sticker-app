from flask import render_template
from flask_login import login_required
from decimal import Decimal

from app.models import PrintJob, Product
from .decorators import store_admin_required

from . import main

@main.route('/analytics')
@login_required
@store_admin_required
def analytics_dashboard():
    """
    View function for the analytics dashboard.
    Only store admin can view analytics.
    """
    try:
        total_print_jobs = PrintJob.query.count()
        total_stickers = sum(job.quantity for job in PrintJob.query.all())

        # Calculate total value (number of stickers * value of product)
        total_value = Decimal('0.00')
        print_jobs = PrintJob.query.all()
        for job in print_jobs:
            if job.product:  # Use the relationship instead of querying by name
                total_value += Decimal(str(job.quantity)) * job.product.rate

        return render_template(
            'analytics.html',
            total_print_jobs=total_print_jobs,
            total_stickers=total_stickers,
            total_value=float(total_value)  # Convert to float for template display
        )
    except Exception as e:
        current_app.logger.error(f"Error in analytics dashboard: {str(e)}")
        flash('Error loading analytics data.', 'danger')
        return redirect(url_for('main.index'))
