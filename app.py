from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'recipe-manager-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/recipes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    cooking_time = db.Column(db.Integer)
    difficulty = db.Column(db.String(20))
    category = db.Column(db.String(50))
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    my_recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    public_recipes = Recipe.query.filter_by(is_public=True).filter(Recipe.user_id != current_user.id).all()
    return render_template('dashboard.html', my_recipes=my_recipes, public_recipes=public_recipes)

@app.route('/add_recipe', methods=['GET', 'POST'])
@login_required
def add_recipe():
    if request.method == 'POST':
        recipe = Recipe(
            title=request.form['title'],
            description=request.form['description'],
            ingredients=request.form['ingredients'],
            instructions=request.form['instructions'],
            cooking_time=request.form.get('cooking_time', 0),
            difficulty=request.form['difficulty'],
            category=request.form['category'],
            is_public='is_public' in request.form,
            user_id=current_user.id
        )
        db.session.add(recipe)
        db.session.commit()
        flash('Recipe added successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('add_recipe.html')

@app.route('/recipe/<int:recipe_id>')
@login_required
def view_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if not recipe.is_public and recipe.user_id != current_user.id:
        flash('You do not have permission to view this recipe')
        return redirect(url_for('dashboard'))
    return render_template('view_recipe.html', recipe=recipe)
@app.route('/edit_recipe/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.user_id != current_user.id:
        flash('You can only edit your own recipes')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        recipe.title = request.form['title']
        recipe.description = request.form['description']
        recipe.ingredients = request.form['ingredients']
        recipe.instructions = request.form['instructions']
        recipe.cooking_time = request.form.get('cooking_time', 0)
        recipe.difficulty = request.form['difficulty']
        recipe.category = request.form['category']
        recipe.is_public = 'is_public' in request.form
        
        db.session.commit()
        flash('Recipe updated successfully!')
        return redirect(url_for('view_recipe', recipe_id=recipe.id))
    
    return render_template('edit_recipe.html', recipe=recipe)

@app.route('/my_recipes')
@login_required
def my_recipes():
    recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    return render_template('my_recipes.html', recipes=recipes)

@app.route('/explore')
@login_required
def explore():
    recipes = Recipe.query.filter_by(is_public=True).filter(Recipe.user_id != current_user.id).all()
    return render_template('explore.html', recipes=recipes)
# Add this BEFORE the if __name__ == '__main__': line
@app.before_first_request
def create_tables():
    db.create_all()

# OR if that doesn't work, use this:
with app.app_context():
    db.create_all()
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
