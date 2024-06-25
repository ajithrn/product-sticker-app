from flask import render_template
from flask_login import login_required

from app.models import PrintJob, Product

from . import main

@main.route('/analytics')
@login_required
def analytics_dashboard():
    """
    View function for the analytics dashboard.
    """
    total_print_jobs = PrintJob.query.count()
    total_stickers = sum(job.quantity for job in PrintJob.query.all())

    # Calculate total value (number of stickers * value of product)
    total_value = 0
    print_jobs = PrintJob.query.all()
    for job in print_jobs:
        product = Product.query.filter_by(name=job.product_name).first()
        if product:
            total_value += job.quantity * float(product.rate)

    return render_template(
        'analytics.html',
        total_print_jobs=total_print_jobs,
        total_stickers=total_stickers,
        total_value=total_value
    )
