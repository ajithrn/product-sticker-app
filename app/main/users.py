from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_paginate import Pagination, get_page_parameter
from werkzeug.security import generate_password_hash

from app import db
from app.models import User
from app.forms import  ProfileForm, UserForm

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
        current_user.name = form.name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.profile'))
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('user_profile.html', form=form)


@main.route('/user_management')
@login_required
def user_management():
    """
    View function for the user management page.
    Displays a list of all users. Only accessible by the store admin.
    """
    if not current_user.is_authenticated or current_user.role != 'store_admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))

    page = request.args.get(get_page_parameter(), type=int, default=1)
    users_pagination = User.query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    users = users_pagination.items
    pagination = Pagination(
        page=page,
        total=users_pagination.total,
        search=False,
        per_page=PER_PAGE,
        css_framework='bootstrap4'
    )
    return render_template('user_management.html', users=users, pagination=pagination)


@main.route('/user_management/new', methods=['GET', 'POST'])
@login_required
def new_user():
    """
    View function for creating a new user.
    Only accessible by the store admin.
    """
    if not current_user.is_authenticated or current_user.role != 'store_admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))
    
    form = UserForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            role=form.role.data,
            name=form.name.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash('New user has been created!', 'success')
        return redirect(url_for('main.user_management'))
    return render_template('user_form.html', form=form, title="Create New User")


@main.route('/user_management/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """
    View function for editing an existing user.
    Only accessible by the store admin.
    """
    if not current_user.is_authenticated or current_user.role != 'store_admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)
    form = UserForm()
    if form.validate_on_submit():
        # Update fields except password
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.name = form.name.data

        # Update password only if provided
        if form.password.data:
            user.password = generate_password_hash(form.password.data)

        db.session.commit()
        flash('User details have been updated!', 'success')
        return redirect(url_for('main.user_management'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role
        form.name.data = user.name
    return render_template('user_form.html', form=form, title="Edit User")


@main.route('/user_management/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """
    View function for deleting a user.
    Only accessible by the store admin.
    """
    if not current_user.is_authenticated or current_user.role != 'store_admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User has been deleted!', 'success')
    return redirect(url_for('main.user_management'))