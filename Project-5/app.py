"""Flask app for the Ames classifieds demo.

Routes:
  GET  /                              homepage with all 5 sections
  GET  /s/<section_slug>              categories within a section
  GET  /c/<category_slug>             listings within a category
  GET  /l/<id>                        listing detail
  GET  /search?q=...                  search across title/description/city
  GET  /login | POST /login           login form
  GET  /register | POST /register     registration form
  GET  /logout                        log out
  GET  /new | POST /new               new listing (login required)
"""

import json
import os

from flask import (
    Flask, abort, flash, redirect, render_template, request, session, url_for,
)
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

import db
import gcs
from config import SECTIONS, CATEGORIES, categories_for_section

load_dotenv()

app = Flask(__name__, static_url_path="/static")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
bcrypt = Bcrypt(app)

CITY_DEFAULT = "Ames, IA"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def current_user():
    return session.get("username")


def require_login():
    if not current_user():
        return redirect(url_for("login", next=request.path))
    return None


def fetch_listing(listing_id):
    row = db.query_one(
        """
        SELECT l.*, c.slug AS category_slug, c.name AS category_name,
               s.slug AS section_slug, s.name AS section_name,
               u.username AS posted_by
        FROM listings l
        JOIN categories c ON c.id = l.category_id
        JOIN sections   s ON s.id = c.section_id
        LEFT JOIN users u ON u.id = l.user_id
        WHERE l.id = %s
        """,
        (listing_id,),
    )
    if row and isinstance(row.get("attributes"), str):
        row["attributes"] = json.loads(row["attributes"])
    return row


# Make a couple of values available to every template
@app.context_processor
def inject_globals():
    return {
        "SECTIONS": SECTIONS,
        "current_user": current_user(),
    }


# ---------------------------------------------------------------------------
# Public read-only routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    counts = {
        row["slug"]: row["n"]
        for row in db.query_all(
            """
            SELECT s.slug, COUNT(l.id) AS n
            FROM sections s
            LEFT JOIN categories c ON c.section_id = s.id
            LEFT JOIN listings   l ON l.category_id = c.id
            GROUP BY s.slug
            """
        )
    }
    section_data = []
    for section in SECTIONS:
        section_data.append({
            "slug": section["slug"],
            "name": section["name"],
            "count": counts.get(section["slug"], 0),
            "categories": [
                {"slug": slug, "name": cat["name"]}
                for slug, cat in categories_for_section(section["slug"])
            ],
        })
    return render_template("home.html", sections=section_data)


@app.route("/s/<section_slug>")
def view_section(section_slug):
    section = next((s for s in SECTIONS if s["slug"] == section_slug), None)
    if not section:
        abort(404)

    cats = categories_for_section(section_slug)
    counts = {
        row["slug"]: row["n"]
        for row in db.query_all(
            """
            SELECT c.slug, COUNT(l.id) AS n
            FROM categories c
            LEFT JOIN listings l ON l.category_id = c.id
            JOIN sections s ON s.id = c.section_id
            WHERE s.slug = %s
            GROUP BY c.slug
            """,
            (section_slug,),
        )
    }
    cats_data = [
        {"slug": slug, "name": cat["name"], "count": counts.get(slug, 0)}
        for slug, cat in cats
    ]
    return render_template("section.html", section=section, categories=cats_data)


@app.route("/c/<category_slug>")
def view_category(category_slug):
    cat = CATEGORIES.get(category_slug)
    if not cat:
        abort(404)
    section = next(s for s in SECTIONS if s["slug"] == cat["section"])

    rows = db.query_all(
        """
        SELECT l.id, l.title, l.price, l.city, l.image_url, l.created_at
        FROM listings l
        JOIN categories c ON c.id = l.category_id
        WHERE c.slug = %s
        ORDER BY l.created_at DESC
        LIMIT 100
        """,
        (category_slug,),
    )
    return render_template(
        "category.html",
        category={"slug": category_slug, "name": cat["name"]},
        section=section,
        listings=rows,
    )


@app.route("/l/<int:listing_id>")
def view_listing(listing_id):
    row = fetch_listing(listing_id)
    if not row:
        abort(404)
    cat_def = CATEGORIES.get(row["category_slug"])
    return render_template("listing.html", listing=row, attribute_defs=cat_def["attributes"])


@app.route("/search")
def search():
    q = (request.args.get("q") or "").strip()
    rows = []
    if q:
        like = f"%{q}%"
        rows = db.query_all(
            """
            SELECT l.id, l.title, l.price, l.city, l.image_url, l.created_at,
                   c.name AS category_name, c.slug AS category_slug
            FROM listings l
            JOIN categories c ON c.id = l.category_id
            WHERE l.title       LIKE %s
               OR l.description LIKE %s
               OR l.city        LIKE %s
            ORDER BY l.created_at DESC
            LIMIT 100
            """,
            (like, like, like),
        )
    return render_template("search.html", q=q, listings=rows)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = db.query_one(
            "SELECT id, username, password_hash FROM users WHERE username = %s",
            (username,),
        )
        if user and bcrypt.check_password_hash(user["password_hash"], password):
            session["username"] = user["username"]
            session["user_id"] = user["id"]
            nxt = request.args.get("next") or url_for("home")
            return redirect(nxt)
        error = "Invalid username or password."
    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm  = request.form.get("confirm") or ""

        if len(username) < 3:
            error = "Username must be at least 3 characters."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif db.query_one("SELECT id FROM users WHERE username = %s", (username,)):
            error = "Username already exists."
        else:
            hashed = bcrypt.generate_password_hash(password).decode("utf-8")
            user_id = db.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, hashed),
            )
            session["username"] = username
            session["user_id"] = user_id
            return redirect(url_for("home"))
    return render_template("register.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# New listing (registered users only)
# ---------------------------------------------------------------------------

@app.route("/new", methods=["GET", "POST"])
def new_listing():
    redirect_resp = require_login()
    if redirect_resp:
        return redirect_resp

    selected_slug = request.values.get("category") or ""
    cat_def = CATEGORIES.get(selected_slug)

    if request.method == "POST":
        errors = []

        if not cat_def:
            errors.append("Please choose a valid category.")
            return render_template(
                "new_listing.html",
                categories=CATEGORIES, selected=selected_slug,
                cat_def=None, errors=errors, form=request.form,
            )

        title       = (request.form.get("title") or "").strip()
        price_raw   = (request.form.get("price") or "").strip()
        city        = (request.form.get("city") or "").strip()
        phone       = (request.form.get("phone") or "").strip()
        description = (request.form.get("description") or "").strip()

        if not title:       errors.append("Title is required.")
        if not city:        errors.append("City is required.")
        if not phone:       errors.append("Phone number is required.")
        if not description: errors.append("Description is required.")
        try:
            price = float(price_raw)
            if price < 0:
                raise ValueError()
        except ValueError:
            errors.append("Price must be a non-negative number.")
            price = None

        attrs = {}
        for spec in cat_def["attributes"]:
            val = (request.form.get(spec["key"]) or "").strip()
            if not val:
                errors.append(f"{spec['label']} is required.")
                continue
            if spec["type"] == "number":
                try:
                    val = float(val)
                except ValueError:
                    errors.append(f"{spec['label']} must be a number.")
                    continue
            if spec["type"] == "select" and val not in spec.get("options", []):
                errors.append(f"{spec['label']} must be one of the listed options.")
                continue
            attrs[spec["key"]] = val

        image_url = None
        upload = request.files.get("image")
        if upload and upload.filename:
            if not gcs.allowed_file(upload.filename):
                errors.append("Image must be png, jpg, jpeg, gif, or webp.")
            else:
                try:
                    image_url = gcs.upload_file(upload)
                except Exception as e:
                    errors.append(f"Image upload failed: {e}")

        if errors:
            return render_template(
                "new_listing.html",
                categories=CATEGORIES, selected=selected_slug,
                cat_def=cat_def, errors=errors, form=request.form,
            )

        cat_row = db.query_one(
            "SELECT id FROM categories WHERE slug = %s",
            (selected_slug,),
        )
        listing_id = db.execute(
            """
            INSERT INTO listings
              (category_id, user_id, title, price, city, phone,
               description, image_url, attributes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                cat_row["id"],
                session.get("user_id"),
                title,
                price,
                city,
                phone,
                description,
                image_url,
                json.dumps(attrs),
            ),
        )
        return redirect(url_for("view_listing", listing_id=listing_id))

    return render_template(
        "new_listing.html",
        categories=CATEGORIES,
        selected=selected_slug,
        cat_def=cat_def,
        errors=None,
        form={"city": CITY_DEFAULT},
    )


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
