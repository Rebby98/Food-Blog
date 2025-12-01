
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from flask_login import UserMixin
from flask_login import LoginManager
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash






app = Flask(__name__)
app.secret_key = "becca.2029"

# SQLite database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foodblog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Set the upload folder path
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # create folder if it doesn't exist

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



login_manager = LoginManager(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page."


@login_manager.user_loader
def load_user(user_id):
    # Try loading from User first
    user = User.query.get(int(user_id))
    if user:
        return user
    
    # If not found, check Admin table
    return Admin.query.get(int(user_id))








class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)



class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    reply = db.Column(db.Text)  # admin’s response
    status = db.Column(db.String(20), default='Pending')  # e.g., Pending, Replied
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)



# Recipe Model


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f" {self.name}>"


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    cuisine = db.Column(db.String(50), nullable=True)   # Kenyan, African, International
    diet_type = db.Column(db.String(50), nullable=True) # Vegetarian, Vegan, etc.
    prep_time = db.Column(db.String(50), nullable=True)
    image = db.Column(db.String(200), nullable=True)    # store image filename

    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    category = db.relationship("Category", backref=db.backref("recipes", lazy=True))

    

# Blog Model
class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=True, default="Admin")
    date_posted = db.Column(db.DateTime, default=db.func.current_timestamp())
    image = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(100), nullable=True)  # <--- Add this



class SavedRecipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)

    user = db.relationship('User', backref='saved_recipes', lazy=True)
    recipe = db.relationship('Recipe', backref='saved_by', lazy=True)


@app.route('/')
def home():
    # Fetch categories
    categories = Category.query.all()

    # Fetch recipes/blogs (your existing code)
    featured_recipes = Recipe.query.limit(3).all()
    latest_blogs = Blog.query.order_by(Blog.date_posted.desc()).limit(3).all()

    return render_template(
        'home.html',
        categories=categories,
        featured_recipes=featured_recipes,
        latest_blogs=latest_blogs
    )




@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/submit_comment', methods=['POST'])
def submit_comment():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    new_comment = Comment(name=name, email=email, message=message)
    db.session.add(new_comment)
    db.session.commit()

    flash("Your message has been sent successfully!", "success")
    return redirect(url_for('about'))    

    

@app.route('/recipes')
def recipes():
    all_recipes = Recipe.query.all()  
    return render_template('recipes.html', recipes=all_recipes)


@app.route('/recipe/<int:recipe_id>')
@login_required
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template('single_recipe.html', recipe=recipe)



@app.route('/search_recipes')
def search_recipes():
    query = request.args.get('q', '').lower()
    if not query:
        recipes = Recipe.query.all()
    else:
        recipes = Recipe.query.filter(
            (Recipe.title.ilike(f'%{query}%')) |
            (Recipe.ingredients.ilike(f'%{query}%')) |
            (Recipe.description.ilike(f'%{query}%'))
        ).all()

    return jsonify([
        {
            'id': r.id,
            'title': r.title,
            'description': r.description,
            'image': r.image
        } for r in recipes
    ])



@app.route('/save_recipe/<int:recipe_id>', methods=['POST'])
@login_required
def save_recipe(recipe_id):
    existing = SavedRecipe.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    if existing:
        return jsonify({'message': 'You already saved this recipe! 😄'})
    
    new_save = SavedRecipe(user_id=current_user.id, recipe_id=recipe_id)
    db.session.add(new_save)
    db.session.commit()
    
    return jsonify({'message': 'Recipe saved successfully! ❤️'})


@app.route('/saved_recipes')
@login_required
def saved_recipes():
    saved = SavedRecipe.query.filter_by(user_id=current_user.id).all()
    recipes = [s.recipe for s in saved]
    return render_template('saved_recipes.html', saved_recipes=recipes)

@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template('view_recipe.html', recipe=recipe)



# Show recipes by category
@app.route("/category/<int:category_id>")
def recipes_by_category(category_id):
    category = Category.query.get_or_404(category_id)
    recipes = Recipe.query.filter_by(category_id=category.id).all()
    return render_template("recipes_by_category.html", category=category, recipes=recipes)




@app.route('/blog')
def blog():
    blogs = Blog.query.order_by(Blog.date_posted.desc()).all()
    return render_template('blog.html', blogs=blogs)



@app.route('/blog/<int:post_id>')
@login_required
def single_post(post_id):
    blog = Blog.query.get_or_404(post_id)
    return render_template('single_post.html', blog=blog)




@app.route('/meal_planner')
def meal_planner():
    return render_template('meal_planner.html')   

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            login_user(admin)
            flash("Logged in successfully!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid username or password", "danger")

    return render_template('admin/login.html')



@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))




@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            flash("Username or email already exists", "danger")
            return redirect(url_for("register"))

        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            session["user_id"] = user.id
            flash("Login successful!", "success")
            return redirect(url_for("home"))  # redirect to home page or user dashboard
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))




@app.route('/admin/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            ingredients = request.form.get('ingredients')
            instructions = request.form.get('instructions')
            cuisine = request.form.get('cuisine')
            category_id = request.form.get('category_id')    # ✅ safe fallback
            diet_type = request.form.get('diet_type')
            prep_time = request.form.get('prep_time')

            category_id = request.form.get('category_id')

            # Handle image upload
            image = request.files.get('image')
            image_filename = None
            if image and image.filename != '':
                image_filename = image.filename
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

            # Save to DB
            new_recipe = Recipe(
                title=title,
                description=description,
                ingredients=ingredients,
                instructions=instructions,
                cuisine=cuisine,
                category_id=category_id,
                diet_type=diet_type,
                prep_time=prep_time,
                image=image_filename
            )
            db.session.add(new_recipe)
            db.session.commit()

            flash("Recipe added successfully!", "success")
            return redirect(url_for('manage_recipes'))  # or wherever you list recipes

        except Exception as e:
            flash(f"Error adding recipe: {e}", "danger")
            return redirect(url_for('add_recipe'))

    categories = Category.query.all()
    return render_template('admin/add_recipe.html', categories=categories)


@app.route('/check')
def check():
    if current_user.is_authenticated:
        return f"Logged in as {current_user.username}"
    return "No one is logged in"



@app.route('/admin/manage_recipes')
def manage_recipes():
    recipes = Recipe.query.all()
    return render_template('admin/manage_recipes.html', recipes=recipes)


@app.route('/admin/add_blog', methods=['GET', 'POST'])
def add_blog():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = "Admin"  # or from a login system later

        # Handle file upload
        image_file = request.files['image']
        image = None
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            image = filename

        # If you added category to your model
        category = request.form.get('category', None)

        new_blog = Blog(
            title=title,
            content=content,
            author=author,
            image=image,
            category=category  # only if you added it to model
        )

        db.session.add(new_blog)
        db.session.commit()
        flash("Blog added successfully!", "success")
        return redirect(url_for('manage_blogs'))

    return render_template('admin/add_blog.html')

@app.route('/admin/edit_blog/<int:blog_id>', methods=['GET', 'POST'])
def edit_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if request.method == 'POST':
        blog.title = request.form['title']
        blog.content = request.form['content']
        blog.category = request.form['category']
        # handle image if needed
        db.session.commit()
        flash("Blog updated successfully!", "success")
        return redirect(url_for('manage_blogs'))
    return render_template('admin/edit_blog.html', blog=blog)

@app.route('/admin/delete_blog/<int:blog_id>', methods=['POST'])
def delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    db.session.delete(blog)
    db.session.commit()
    flash("Blog deleted successfully!", "success")
    return redirect(url_for('manage_blogs'))



@app.route('/admin/edit_recipe/<int:recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    categories = Category.query.all()  # ✅ fetch all categories

    if request.method == 'POST':
        recipe.title = request.form['title']
        recipe.description = request.form['description']
        recipe.ingredients = request.form['ingredients']
        recipe.instructions = request.form['instructions']
        recipe.cuisine = request.form['cuisine']
        recipe.diet_type = request.form['diet_type']
        recipe.prep_time = request.form['prep_time']

        # ✅ update category
        recipe.category_id = int(request.form['category_id'])

        # ✅ handle image update
        image = request.files.get('image')
        if image and image.filename != '':
            image_filename = image.filename
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            recipe.image = image_filename

        db.session.commit()
        flash("Recipe updated successfully!", "success")
        return redirect(url_for('manage_recipes'))

    return render_template('admin/edit_recipe.html', recipe=recipe, categories=categories)


@app.route('/admin/delete_recipe/<int:recipe_id>', methods=['POST', 'GET'])
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    db.session.delete(recipe)
    db.session.commit()
    return redirect(url_for('manage_recipes'))


@app.route('/admin/manage_blogs')
def manage_blogs():
    blogs = Blog.query.all()
    return render_template('admin/manage_blogs.html', blogs=blogs) 


@app.route('/admin/comments')
@login_required  # only admin
def view_comments():
    comments = Comment.query.order_by(Comment.date_posted.desc()).all()
    return render_template('admin/admin_comments.html', comments=comments)

@app.route('/admin/reply_comment/<int:comment_id>', methods=['POST'])
@login_required
def reply_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    reply = request.form['reply']
    comment.reply = reply
    comment.status = 'Replied'
    db.session.commit()
    flash("Reply sent successfully!", "success")
    return redirect(url_for('view_comments'))


if __name__ == '__main__':
    app.run(debug=True)


   
