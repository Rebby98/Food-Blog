
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.utils import secure_filename
import os
from flask_login import UserMixin
from flask_login import LoginManager
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer






app = Flask(__name__)
import os

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "becca.2029"
)

app.secret_key = app.config["SECRET_KEY"]

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///foodblog.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_USERNAME")

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

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
    is_verified = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def get_reset_token(self):
        return serializer.dumps(self.email, salt='password-reset')

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        try:
            email = serializer.loads(
                token,
                salt='password-reset',
                max_age=expires_sec
            )
        except:
            return None

        return User.query.filter_by(email=email).first()

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
    cuisine = db.Column(db.String(50), nullable=True)
    diet_type = db.Column(db.String(50), nullable=True)
    prep_time = db.Column(db.String(50), nullable=True)
    goal = db.Column(db.String(100))
    image = db.Column(db.String(200), nullable=True)

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category.id"),
        nullable=False
    )

    category = db.relationship(
        "Category",
        backref=db.backref("recipes", lazy=True)
    )

    # NEW
    saved_by = db.relationship(
        "SavedRecipe",
        back_populates="recipe",
        cascade="all, delete-orphan"
    )

    

# Blog Model
class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=True, default="Becca")
    date_posted = db.Column(db.DateTime, default=db.func.current_timestamp())
    image = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(100), nullable=True)  # <--- Add this



class SavedRecipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipe.id"),
        nullable=False
    )

    user = db.relationship(
        "User",
        backref="saved_recipes"
    )

    recipe = db.relationship(
        "Recipe",
        back_populates="saved_by"
    )



def send_reset_email(user):

    token = serializer.dumps(user.email, salt="password-reset")

    reset_url = url_for(
        "reset_password",
        token=token,
        _external=True
    )

    msg = Message(
        "Reset Your Becca Foodies Password",
        recipients=[user.email]
    )

    msg.body = f"""
Hello {user.username},

Someone requested a password reset for your Becca Foodies account.

Click the link below to reset your password:

{reset_url}

If you did not request this, simply ignore this email.

The link expires in 30 minutes.

Happy Cooking!

Becca Foodies
"""

    mail.send(msg)

def send_verification_email(user):

    token = serializer.dumps(
        user.email,
        salt="email-confirm"
    )

    verify_url = url_for(
        "verify_email",
        token=token,
        _external=True
    )

    msg = Message(
        "Verify your Becca Foodies account",
        recipients=[user.email]
    )

    msg.body = f"""
Hello {user.username},

Welcome to Becca Foodies!

Please click the link below to verify your email address.

{verify_url}

If you did not create this account, simply ignore this email.

Happy Cooking!

Becca Foodies
"""

    mail.send(msg)

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


from sqlalchemy import or_

@app.route("/recipe/<int:recipe_id>")
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)

    all_recipes = Recipe.query.filter(Recipe.id != recipe.id).all()

    scored_recipes = []

    for r in all_recipes:
        score = 0

        if r.category_id == recipe.category_id:
            score += 4

        if r.cuisine == recipe.cuisine:
            score += 3

        if r.goal == recipe.goal:
            score += 2

        if r.diet_type == recipe.diet_type:
            score += 2

        if score > 0:
            scored_recipes.append((score, r))

    scored_recipes.sort(key=lambda x: x[0], reverse=True)

    similar_recipes = [recipe for score, recipe in scored_recipes[:4]]

    return render_template(
        "single_recipe.html",
        recipe=recipe,
        similar_recipes=similar_recipes
    )


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

    existing = SavedRecipe.query.filter_by(
        user_id=current_user.id,
        recipe_id=recipe_id
    ).first()

    if existing:
        flash("Recipe already saved!", "info")
        return redirect(request.referrer)

    new_save = SavedRecipe(
        user_id=current_user.id,
        recipe_id=recipe_id
    )

    db.session.add(new_save)
    db.session.commit()

    flash("Recipe saved successfully! ❤️", "success")

    return redirect(url_for("saved_recipes"))
@app.route('/test_flash')
def test_flash():
    flash("Flash messages are working!", "success")
    return redirect(url_for('saved_recipes'))


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

@app.route('/unsave_recipe/<int:recipe_id>', methods=['POST'])
@login_required
def unsave_recipe(recipe_id):

    saved_recipe = SavedRecipe.query.filter_by(
        user_id=current_user.id,
        recipe_id=recipe_id
    ).first()

    if saved_recipe:
        db.session.delete(saved_recipe)
        db.session.commit()
        flash("Recipe removed from your saved recipes.", "success")
    else:
        flash("Recipe not found in your saved recipes.", "warning")

    return redirect(url_for('saved_recipes'))

# Show recipes by category
@app.route("/category/<int:category_id>")
def recipes_by_category(category_id):
    category = Category.query.get_or_404(category_id)
    recipes = Recipe.query.filter_by(category_id=category.id).all()
    return render_template("recipes_by_category.html", category=category, recipes=recipes)





@app.route('/blog')
def blog():

    search = request.args.get('search', '')

    blogs = Blog.query

    if search:
        blogs = blogs.filter(
            or_(
                Blog.title.ilike(f'%{search}%'),
                Blog.content.ilike(f'%{search}%')
            )
        )

    blogs = blogs.order_by(Blog.date_posted.desc()).all()

    return render_template(
        'blog.html',
        blogs=blogs
    )


@app.route('/blog/<int:post_id>')
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

        # Username already exists
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))

        # Email already exists
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        new_user = User(
            username=username,
            email=email,
            is_verified=False
        )

        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        # Send verification email
        send_verification_email(new_user)

        flash(
            "Registration successful! Please check your email to verify your account.",
            "success"
        )

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/verify-email/<token>")
def verify_email(token):

    try:
        email = serializer.loads(
            token,
            salt="email-confirm",
            max_age=1800
        )

    except Exception:

        flash(
            "Verification link is invalid or has expired.",
            "danger"
        )

        return redirect(url_for("login"))

    user = User.query.filter_by(email=email).first()

    if not user:

        flash(
            "User not found.",
            "danger"
        )

        return redirect(url_for("register"))

    if user.is_verified:

        flash(
            "Your email is already verified.",
            "info"
        )

        return redirect(url_for("login"))

    user.is_verified = True

    db.session.commit()

    flash(
        "Email verified successfully! You can now log in.",
        "success"
    )

    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):

            login_user(user)

            flash(f"Welcome back, {user.username}! 👋", "success")

            next_page = request.args.get("next")

            return redirect(next_page or url_for("home"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email")

        user = User.query.filter_by(email=email).first()

        if user:

            send_reset_email(user)

            flash(
                "A password reset link has been sent to your email.",
                "success"
            )

            return redirect(url_for("login"))

        else:

            flash(
                "No account found with that email.",
                "danger"
            )

    return render_template("forgot_password.html")

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_token(token)

    if user is None:
        flash("That password reset link is invalid or has expired.", "danger")
        return redirect(url_for('forgot_password'))

    if request.method == "POST":
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(request.url)

        user.set_password(password)
        db.session.commit()

        flash("Your password has been reset successfully! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html", token=token)

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


@app.route('/admin/delete_recipe/<int:recipe_id>')
@login_required
def delete_recipe(recipe_id):

    recipe = Recipe.query.get_or_404(recipe_id)

    SavedRecipe.query.filter_by(recipe_id=recipe.id).delete()

    db.session.delete(recipe)

    db.session.commit()

    flash("Recipe deleted successfully.", "success")

    return redirect(url_for("manage_recipes"))


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

print("\n========== ROUTES ==========")
for rule in app.url_map.iter_rules():
    print(rule)
print("============================")
if __name__ == '__main__':
    app.run(debug=True)


   
