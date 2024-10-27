from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, DateField, TextAreaField, BooleanField, DecimalField
from wtforms.validators import DataRequired, Length, ValidationError, Email, EqualTo, Optional, NumberRange
from app.models import User, ProductCategory

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=255)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('store_admin', 'Store Admin'), ('staff', 'Staff')], validators=[DataRequired()])
    submit = SubmitField('Register')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField('Password', validators=[Optional(), Length(min=8, max=255)])
    confirm_password = PasswordField('Confirm Password', validators=[Optional(), EqualTo('password')])
    role = SelectField('Role', choices=[('store_admin', 'Store Admin'), ('staff', 'Staff')], validators=[DataRequired()])
    name = StringField('Name', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Save')

class ProfileForm(FlaskForm):
    name = StringField('Name', validators=[Optional(), Length(max=100)])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField('New Password', validators=[Optional(), Length(min=8, max=255)])
    confirm_password = PasswordField('Confirm New Password', validators=[Optional(), EqualTo('password')])
    submit = SubmitField('Update Profile')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired(), Length(max=100)])
    category_id = StringField('Category', validators=[DataRequired()])
    rate = DecimalField('Rate', validators=[DataRequired(), NumberRange(min=0)], places=2)
    net_weight = StringField('Net Weight (grams)', validators=[DataRequired(), Length(max=20)])
    shelf_life = IntegerField('Shelf Life (days)', validators=[DataRequired(), NumberRange(min=1)])
    ingredients = TextAreaField('Ingredients', validators=[DataRequired()])
    nutritional_facts = TextAreaField('Nutritional Facts (Serving Size: 100g)', validators=[DataRequired()], default=(
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
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    mfg_date = DateField('Manufacturing Date', validators=[DataRequired()])
    exp_date = DateField('Expiry Date', validators=[DataRequired()])
    quantity = IntegerField('Number of Stickers', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Print')

class PrintForm(FlaskForm):
    product_search = StringField('Product Search')
    mfg_date = DateField('Manufacturing Date')
    exp_date = DateField('Expiry Date')
    quantity = IntegerField('Number of Stickers per Product', validators=[DataRequired(), NumberRange(min=1)])
    add_product = SubmitField('Add Product')
    print_stickers = SubmitField('Print Stickers')

class ProductSearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Save')

class StoreInfoForm(FlaskForm):
    name = StringField('Store Name', validators=[DataRequired(), Length(max=100)])
    address = TextAreaField('Address', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=20)])
    gst_number = StringField('GST Number', validators=[DataRequired(), Length(min=15, max=20)])
    fssai_number = StringField('FSSAI Number', validators=[DataRequired(), Length(min=14, max=20)])
    submit = SubmitField('Save Store Info')

class StickerDesignForm(FlaskForm):
    print_nutritional_heading = BooleanField('Print Nutritional Facts Heading')
    print_allergen_heading = BooleanField('Print Allergen Information Heading')
    print_ingredients_heading = BooleanField('Print Ingredients Heading')
    submit = SubmitField('Save Design')
