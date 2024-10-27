from flask import render_template, jsonify, request, current_app, flash, redirect, url_for
from flask_login import login_required
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import calendar

from app.models import PrintJob, Product
from app import db
from .decorators import store_admin_required
from . import main

def get_date_range(period='day', start_date=None, end_date=None):
    today = datetime.now()
    
    if start_date and end_date:
        return datetime.strptime(start_date, '%Y-%m-%d'), datetime.strptime(end_date, '%Y-%m-%d')
    
    if period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today - timedelta(days=30)
    elif period == 'year':
        start_date = today - timedelta(days=365)
    elif period == 'all':
        # Get the date of the first print job or 1 year ago if no jobs
        first_job = db.session.query(func.min(PrintJob.created_at)).scalar()
        start_date = first_job if first_job else today - timedelta(days=365)
    else:  # Default to day
        start_date = today - timedelta(days=1)
    
    return start_date, today

def get_product_stats():
    """Get statistics grouped by product"""
    try:
        product_stats = (
            db.session.query(
                Product.name,
                func.coalesce(func.sum(PrintJob.quantity), 0).label('total_quantity'),
                func.count(PrintJob.id).label('job_count'),
                func.coalesce(func.sum(PrintJob.quantity * Product.rate), 0).label('total_value')
            )
            .outerjoin(PrintJob)
            .group_by(Product.name)
            .order_by(desc(func.coalesce(func.sum(PrintJob.quantity), 0)))
            .all()
        )
        
        return [
            {
                'product': stat[0],
                'quantity': int(stat[1] or 0),
                'jobs': int(stat[2] or 0),
                'value': float(stat[3] or 0)
            }
            for stat in product_stats
        ]
    except Exception as e:
        current_app.logger.error(f"Error in get_product_stats: {str(e)}")
        return []

def get_time_series_data(period='day', start_date=None, end_date=None):
    """Get time series data for print jobs"""
    try:
        start_date, end_date = get_date_range(period, start_date, end_date)
        
        jobs_data = (
            db.session.query(
                func.date(PrintJob.created_at).label('date'),
                func.coalesce(func.sum(PrintJob.quantity), 0).label('quantity'),
                func.count(PrintJob.id).label('count'),
                func.coalesce(func.sum(PrintJob.quantity * Product.rate), 0).label('value')
            )
            .join(Product)
            .filter(PrintJob.created_at.between(start_date, end_date))
            .group_by(func.date(PrintJob.created_at))
            .order_by(func.date(PrintJob.created_at))
            .all()
        )
        
        return [
            {
                'date': date.strftime('%Y-%m-%d'),
                'quantity': int(quantity or 0),
                'jobs': int(count or 0),
                'value': float(value or 0)
            }
            for date, quantity, count, value in jobs_data
        ]
    except Exception as e:
        current_app.logger.error(f"Error in get_time_series_data: {str(e)}")
        return []

@main.route('/analytics/data')
@login_required
@store_admin_required
def analytics_data():
    """API endpoint for analytics data"""
    try:
        period = request.args.get('period', 'day')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        time_series = get_time_series_data(period, start_date, end_date)
        product_stats = get_product_stats()
        
        # Calculate totals for the selected period
        total_stickers = sum(day['quantity'] for day in time_series)
        total_jobs = sum(day['jobs'] for day in time_series)
        total_value = sum(day['value'] for day in time_series)
        
        return jsonify({
            'success': True,
            'time_series': time_series,
            'product_stats': product_stats,
            'period_totals': {
                'stickers': total_stickers,
                'jobs': total_jobs,
                'value': total_value
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error in analytics_data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main.route('/analytics')
@login_required
@store_admin_required
def analytics_dashboard():
    """
    View function for the analytics dashboard.
    Only store admin can view analytics.
    """
    try:
        # Get total print jobs
        total_print_jobs = db.session.query(func.count(PrintJob.id)).scalar() or 0

        # Get total stickers
        total_stickers = db.session.query(func.sum(PrintJob.quantity)).scalar() or 0

        # Calculate total value
        total_value = (
            db.session.query(func.sum(PrintJob.quantity * Product.rate))
            .join(Product, PrintJob.product_id == Product.id)
            .scalar() or Decimal('0.00')
        )

        return render_template(
            'analytics.html',
            total_print_jobs=total_print_jobs,
            total_stickers=total_stickers,
            total_value=float(total_value)
        )
    except Exception as e:
        current_app.logger.error(f"Error in analytics dashboard: {str(e)}")
        flash('Error loading analytics data.', 'danger')
        return redirect(url_for('main.index'))
