from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError, Email, EqualTo, Optional
from app.models import User, ProductCategory

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=150)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('store_admin', 'Store Admin'), ('staff', 'Staff')], validators=[DataRequired()])
    submit = SubmitField('Register')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Optional(), Length(min=6, max=150)])
    confirm_password = PasswordField('Confirm Password', validators=[Optional(), EqualTo('password')])
    role = SelectField('Role', choices=[('store_admin', 'Store Admin'), ('staff', 'Staff')], validators=[DataRequired()])
    name = StringField('Name')
    submit = SubmitField('Save')

class ProfileForm(FlaskForm):
    name = StringField('Name')
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('New Password', validators=[Optional(), Length(min=6, max=150)])
    confirm_password = PasswordField('Confirm New Password', validators=[Optional(), EqualTo('password')])
    submit = SubmitField('Update Profile')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    rate = StringField('Rate', validators=[DataRequired()])
    net_weight = StringField('Net Weight (grams)', validators=[DataRequired()])
    shelf_life = IntegerField('Shelf Life (days)', validators=[DataRequired()])
    ingredients = TextAreaField('Ingredients', validators=[DataRequired()])
    nutritional_facts = TextAreaField('Nutritional Facts', validators=[DataRequired()], default=(
        "Energy Value:    kcal\n"
        "Protein:         g\n"
        "Carbohydrates:   g\n"
        "Sugars:          g\n"
        "Total Fat:       g\n"
        "Saturated Fats:  g\n"
        "Trans Fats:      g\n"
        "Cholesterol:     mg\n"
        "Sodium:          mg"
    ))
    allergen_information = TextAreaField('Allergen Information', validators=[DataRequired()])
    submit = SubmitField('Save')

class SingleProductPrintForm(FlaskForm):
    """
    Form for printing stickers for a single product.
    """
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    mfg_date = DateField('Manufacturing Date', validators=[DataRequired()])
    exp_date = DateField('Expiry Date', validators=[DataRequired()])
    quantity = IntegerField('Number of Stickers', validators=[DataRequired()])
    submit = SubmitField('Print')

class PrintForm(FlaskForm):
    product_search = StringField('Product Search')  # AJAX search field
    mfg_date = DateField('Manufacturing Date')
    exp_date = DateField('Expiry Date')
    quantity = IntegerField('Number of Stickers per Product', validators=[DataRequired()])
    add_product = SubmitField('Add Product')
    print_stickers = SubmitField('Print Stickers')

class ProductSearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired()])
    submit = SubmitField('Save')
