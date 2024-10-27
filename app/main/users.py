from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from flask_paginate import Pagination, get_page_parameter
from werkzeug.security import generate_password_hash
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import User
from app.forms import ProfileForm, UserForm
from .decorators import store_admin_required

from . import main

# Constants for pagination
PER_PAGE = 10

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    View function for the user profile page.
    Allows users to update their profile information.
    """
    form = ProfileForm()
    if form.validate_on_submit():
        try:
            # Check if username is taken by another user
            if form.username.data != current_user.username:
                existing_user = User.query.filter_by(username=form.username.data).first()
                if existing_user:
                    flash('Username already taken.', 'danger')
                    return render_template('user_profile.html', form=form)

            # Check if email is taken by another user
            if form.email.data != current_user.email:
                existing_user = User.query.filter_by(email=form.email.data).first()
                if existing_user:
                    flash('Email already registered.', 'danger')
                    return render_template('user_profile.html', form=form)

            current_user.name = form.name.data
            current_user.username = form.username.data
            current_user.email = form.email.data
            if form.password.data:
                current_user.password = generate_password_hash(form.password.data)
            
            db.session.commit()
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('main.profile'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating profile: {str(e)}')
            flash(f'Error updating profile: {str(e)}', 'danger')
    
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    return render_template('user_profile.html', form=form)

@main.route('/user_management')
@login_required
@store_admin_required
def user_management():
    """
    View function for the user management page.
    Displays a list of all users with their print job counts.
    """
    try:
        page = request.args.get(get_page_parameter(), type=int, default=1)
        users_pagination = User.query.order_by(
            desc(User.updated_at)
        ).paginate(
            page=page,
            per_page=PER_PAGE,
            error_out=False
        )
        
        return render_template(
            'user_management.html',
            users=users_pagination.items,
            pagination=Pagination(
                page=page,
                total=users_pagination.total,
                search=False,
                per_page=PER_PAGE,
                css_framework='bootstrap4'
            )
        )
    except Exception as e:
        current_app.logger.error(f'Error in user management: {str(e)}')
        flash('Error loading user list.', 'danger')
        return redirect(url_for('main.index'))

@main.route('/user_management/new', methods=['GET', 'POST'])
@login_required
@store_admin_required
def new_user():
    """
    View function for creating a new user.
    """
    form = UserForm()
    if form.validate_on_submit():
        try:
            # Check if username is taken
            if User.query.filter_by(username=form.username.data).first():
                flash('Username already taken.', 'danger')
                return render_template('user_form.html', form=form, title="Create New User")

            # Check if email is taken
            if User.query.filter_by(email=form.email.data).first():
                flash('Email already registered.', 'danger')
                return render_template('user_form.html', form=form, title="Create New User")

            # Create new user
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data),
                role=form.role.data,
                name=form.name.data
            )
            
            # Add and commit in separate steps for better error handling
            db.session.add(new_user)
            try:
                db.session.commit()
                current_app.logger.info(f'New user created: {new_user.username}')
                flash('New user has been created!', 'success')
                return redirect(url_for('main.user_management'))
            except IntegrityError:
                db.session.rollback()
                flash('Username or email already exists.', 'danger')
                return render_template('user_form.html', form=form, title="Create New User")
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating user: {str(e)}')
            flash(f'Error creating user: {str(e)}', 'danger')
    
    # If GET request or form validation failed
    return render_template('user_form.html', form=form, title="Create New User")

@main.route('/user_management/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@store_admin_required
def edit_user(user_id):
    """
    View function for editing an existing user.
    """
    user = User.query.get_or_404(user_id)
    form = UserForm()
    
    if form.validate_on_submit():
        try:
            # Check if username is taken by another user
            if form.username.data != user.username:
                existing_user = User.query.filter_by(username=form.username.data).first()
                if existing_user:
                    flash('Username already taken.', 'danger')
                    return render_template('user_form.html', form=form, title="Edit User")

            # Check if email is taken by another user
            if form.email.data != user.email:
                existing_user = User.query.filter_by(email=form.email.data).first()
                if existing_user:
                    flash('Email already registered.', 'danger')
                    return render_template('user_form.html', form=form, title="Edit User")

            # Update user details
            user.username = form.username.data
            user.email = form.email.data
            user.role = form.role.data
            user.name = form.name.data

            if form.password.data:
                user.password = generate_password_hash(form.password.data)

            try:
                db.session.commit()
                current_app.logger.info(f'User updated: {user.username}')
                flash('User details have been updated!', 'success')
                return redirect(url_for('main.user_management'))
            except IntegrityError:
                db.session.rollback()
                flash('Username or email already exists.', 'danger')
                return render_template('user_form.html', form=form, title="Edit User")
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating user: {str(e)}')
            flash(f'Error updating user: {str(e)}', 'danger')
    
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role
        form.name.data = user.name
    
    return render_template('user_form.html', form=form, title="Edit User")

@main.route('/user_management/delete/<int:user_id>', methods=['POST'])
@login_required
@store_admin_required
def delete_user(user_id):
    """
    View function for deleting a user.
    """
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('main.user_management'))

    try:
        user = User.query.get_or_404(user_id)
        print_jobs_count = len(user.print_jobs)
        
        db.session.delete(user)
        db.session.commit()
        
        current_app.logger.info(f'User deleted: {user.username} with {print_jobs_count} print jobs')
        flash(f'User and {print_jobs_count} associated print jobs have been deleted!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting user: {str(e)}')
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('main.user_management'))
