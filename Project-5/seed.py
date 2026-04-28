"""Populate the classifieds database with sections, categories, a demo user,
and at least 3 listings per category (75+ listings total).

Run after schema.sql has been applied:
    python seed.py

Idempotent: re-running leaves data in the same final state (existing rows
are preserved by ON DUPLICATE KEY UPDATE on slugs/usernames; listings are
only inserted if the category currently has fewer than 3 rows).

Image URLs use picsum.photos so the seed runs without contacting GCS.
Replace them with real images by uploading via the web UI.
"""

from __future__ import annotations

import json
import os
import sys

# Allow running this file directly without installing the package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from flask import Flask

import db
from config import SECTIONS, CATEGORIES

load_dotenv()
bcrypt = Bcrypt(Flask(__name__))


# ---------------------------------------------------------------------------
# Listing fixtures: 3 per category. Common cols + category-specific attrs.
# ---------------------------------------------------------------------------

def img(seed: str) -> str:
    return f"https://picsum.photos/seed/{seed}/600/400"


LISTINGS = {
    # ---------- For Sale ----------
    "cars-trucks": [
        {"title": "2015 Honda Civic LX", "price": 9500, "city": "Ames, IA", "phone": "515-555-0101",
         "description": "Single owner, well-maintained, all service records available.",
         "image_url": img("civic"),
         "attributes": {"year": 2015, "make_model": "Honda Civic LX", "color": "Silver", "mileage": 87000, "condition": "Good"}},
        {"title": "2018 Ford F-150 XLT 4x4", "price": 24500, "city": "Ames, IA", "phone": "515-555-0102",
         "description": "Crew cab, tow package, recent tires. Garage kept.",
         "image_url": img("f150"),
         "attributes": {"year": 2018, "make_model": "Ford F-150 XLT", "color": "Blue", "mileage": 64000, "condition": "Like New"}},
        {"title": "2010 Toyota Camry SE", "price": 6800, "city": "Ames, IA", "phone": "515-555-0103",
         "description": "Reliable commuter, fresh oil change, new battery.",
         "image_url": img("camry"),
         "attributes": {"year": 2010, "make_model": "Toyota Camry SE", "color": "White", "mileage": 142000, "condition": "Good"}},
    ],
    "motorcycles": [
        {"title": "2019 Harley-Davidson Iron 883", "price": 7200, "city": "Ames, IA", "phone": "515-555-0201",
         "description": "Black-on-black, low miles, Vance & Hines exhaust.",
         "image_url": img("harley"),
         "attributes": {"year": 2019, "make_model": "Harley Iron 883", "color": "Black", "mileage": 6200, "condition": "Like New"}},
        {"title": "2017 Kawasaki Ninja 650", "price": 4800, "city": "Ames, IA", "phone": "515-555-0202",
         "description": "Great starter sportbike. Fresh chain and tires.",
         "image_url": img("ninja"),
         "attributes": {"year": 2017, "make_model": "Kawasaki Ninja 650", "color": "Green", "mileage": 11500, "condition": "Good"}},
        {"title": "2014 Honda Shadow 750", "price": 3900, "city": "Ames, IA", "phone": "515-555-0203",
         "description": "Comfortable cruiser, saddlebags included.",
         "image_url": img("shadow"),
         "attributes": {"year": 2014, "make_model": "Honda Shadow 750", "color": "Red", "mileage": 18900, "condition": "Good"}},
    ],
    "boats": [
        {"title": "1998 Bayliner Capri 1850", "price": 6500, "city": "Ames, IA", "phone": "515-555-0301",
         "description": "Bowrider with trailer. Recently serviced engine.",
         "image_url": img("bayliner"),
         "attributes": {"year_built": 1998, "make_model": "Bayliner Capri 1850", "color": "White/Blue", "boat_type": "Bowrider", "condition": "Good"}},
        {"title": "2008 Tracker Pro Guide V-16", "price": 8900, "city": "Ames, IA", "phone": "515-555-0302",
         "description": "Aluminum fishing boat. Trolling motor and fish finder.",
         "image_url": img("tracker"),
         "attributes": {"year_built": 2008, "make_model": "Tracker Pro Guide V-16", "color": "Green", "boat_type": "Fishing", "condition": "Like New"}},
        {"title": "2003 Sea-Doo GTI Jet Ski", "price": 3200, "city": "Ames, IA", "phone": "515-555-0303",
         "description": "Two-seater jet ski with trailer.",
         "image_url": img("seadoo"),
         "attributes": {"year_built": 2003, "make_model": "Sea-Doo GTI", "color": "Yellow", "boat_type": "Jet Ski", "condition": "Fair"}},
    ],
    "books": [
        {"title": "Intro to Algorithms (CLRS), 3rd ed.", "price": 35, "city": "Ames, IA", "phone": "515-555-0401",
         "description": "Lightly used textbook. Some highlighting.",
         "image_url": img("clrs"),
         "attributes": {"title_book": "Introduction to Algorithms", "author": "Cormen et al.", "genre": "Computer Science", "format": "Hardcover", "condition": "Good"}},
        {"title": "Dune by Frank Herbert", "price": 8, "city": "Ames, IA", "phone": "515-555-0402",
         "description": "Classic sci-fi paperback. Spine intact.",
         "image_url": img("dune"),
         "attributes": {"title_book": "Dune", "author": "Frank Herbert", "genre": "Science Fiction", "format": "Paperback", "condition": "Like New"}},
        {"title": "Calculus: Early Transcendentals", "price": 45, "city": "Ames, IA", "phone": "515-555-0403",
         "description": "Stewart 8th edition, used for MATH 165/166.",
         "image_url": img("calc"),
         "attributes": {"title_book": "Calculus: Early Transcendentals", "author": "James Stewart", "genre": "Mathematics", "format": "Hardcover", "condition": "Good"}},
    ],
    "furniture": [
        {"title": "IKEA Ektorp 3-seat sofa", "price": 180, "city": "Ames, IA", "phone": "515-555-0501",
         "description": "Beige slipcover, washable. Pet-free, smoke-free home.",
         "image_url": img("ektorp"),
         "attributes": {"item_type": "Sofa", "material": "Wood/Fabric", "color": "Beige", "dimensions": "85\"W x 35\"D x 35\"H", "condition": "Good"}},
        {"title": "Solid oak dining table + 4 chairs", "price": 350, "city": "Ames, IA", "phone": "515-555-0502",
         "description": "Sturdy farmhouse-style set. Minor scratches on legs.",
         "image_url": img("oaktable"),
         "attributes": {"item_type": "Dining set", "material": "Oak", "color": "Natural", "dimensions": "60\"L x 36\"W x 30\"H", "condition": "Like New"}},
        {"title": "Queen-size memory foam mattress", "price": 220, "city": "Ames, IA", "phone": "515-555-0503",
         "description": "Two years old, always with a mattress protector.",
         "image_url": img("mattress"),
         "attributes": {"item_type": "Mattress", "material": "Memory foam", "color": "White", "dimensions": "60\" x 80\" x 12\"", "condition": "Good"}},
    ],

    # ---------- Housing ----------
    "apartments-rent": [
        {"title": "2BR / 1BA near campus", "price": 1100, "city": "Ames, IA", "phone": "515-555-0601",
         "description": "5 min walk to ISU. On-site laundry, parking included.",
         "image_url": img("apt1"),
         "attributes": {"bedrooms": 2, "bathrooms": 1, "sqft": 850, "pets": "Cats only", "available": "Aug 1, 2026"}},
        {"title": "Studio loft downtown", "price": 850, "city": "Ames, IA", "phone": "515-555-0602",
         "description": "Modern downtown studio with exposed brick.",
         "image_url": img("studio"),
         "attributes": {"bedrooms": 1, "bathrooms": 1, "sqft": 480, "pets": "No", "available": "June 15, 2026"}},
        {"title": "3BR / 2BA west Ames", "price": 1450, "city": "Ames, IA", "phone": "515-555-0603",
         "description": "Quiet residential street, garage, fenced backyard.",
         "image_url": img("apt3"),
         "attributes": {"bedrooms": 3, "bathrooms": 2, "sqft": 1300, "pets": "Yes", "available": "July 1, 2026"}},
    ],
    "houses-sale": [
        {"title": "4BR ranch on .25 acre lot", "price": 285000, "city": "Ames, IA", "phone": "515-555-0701",
         "description": "Updated kitchen, finished basement, 2-car garage.",
         "image_url": img("house1"),
         "attributes": {"bedrooms": 4, "bathrooms": 2.5, "sqft": 2100, "lot_size": "0.25 acres", "year_built": 1985}},
        {"title": "Charming 2BR bungalow", "price": 185000, "city": "Ames, IA", "phone": "515-555-0702",
         "description": "Original hardwood floors, walking distance to shops.",
         "image_url": img("house2"),
         "attributes": {"bedrooms": 2, "bathrooms": 1, "sqft": 1100, "lot_size": "0.15 acres", "year_built": 1948}},
        {"title": "New construction 5BR colonial", "price": 425000, "city": "Ames, IA", "phone": "515-555-0703",
         "description": "Brand-new build with smart-home wiring throughout.",
         "image_url": img("house3"),
         "attributes": {"bedrooms": 5, "bathrooms": 3.5, "sqft": 3200, "lot_size": "0.4 acres", "year_built": 2025}},
    ],
    "rooms-roommates": [
        {"title": "Room available in 4BR house", "price": 525, "city": "Ames, IA", "phone": "515-555-0801",
         "description": "Three friendly grad-student housemates, near CyRide.",
         "image_url": img("room1"),
         "attributes": {"rent": 525, "furnished": "No", "private_bath": "No", "available": "Aug 15, 2026", "lease": "12 months"}},
        {"title": "Master bedroom w/ private bath", "price": 700, "city": "Ames, IA", "phone": "515-555-0802",
         "description": "Bright corner room. Utilities split four ways.",
         "image_url": img("room2"),
         "attributes": {"rent": 700, "furnished": "Yes", "private_bath": "Yes", "available": "July 1, 2026", "lease": "9 months"}},
        {"title": "Looking for one roommate", "price": 600, "city": "Ames, IA", "phone": "515-555-0803",
         "description": "Quiet professional looking for a quiet housemate.",
         "image_url": img("room3"),
         "attributes": {"rent": 600, "furnished": "No", "private_bath": "Yes", "available": "Aug 1, 2026", "lease": "6 months"}},
    ],
    "sublets": [
        {"title": "Summer sublet near campus", "price": 600, "city": "Ames, IA", "phone": "515-555-0901",
         "description": "Subletting May-August, fully furnished.",
         "image_url": img("sublet1"),
         "attributes": {"bedrooms": 1, "start_date": "May 15, 2026", "end_date": "Aug 10, 2026", "furnished": "Yes", "utilities": "Yes"}},
        {"title": "Fall semester sublet", "price": 900, "city": "Ames, IA", "phone": "515-555-0902",
         "description": "Studying abroad, need someone to cover lease Aug-Dec.",
         "image_url": img("sublet2"),
         "attributes": {"bedrooms": 2, "start_date": "Aug 20, 2026", "end_date": "Dec 20, 2026", "furnished": "No", "utilities": "Some"}},
        {"title": "Winter break sublet", "price": 400, "city": "Ames, IA", "phone": "515-555-0903",
         "description": "Short-term sublet for visiting researcher.",
         "image_url": img("sublet3"),
         "attributes": {"bedrooms": 1, "start_date": "Dec 15, 2026", "end_date": "Jan 15, 2027", "furnished": "Yes", "utilities": "Yes"}},
    ],
    "vacation-rentals": [
        {"title": "Lakefront cabin near Saylorville", "price": 165, "city": "Ames, IA", "phone": "515-555-1001",
         "description": "Sleeps 6, dock access, peaceful setting.",
         "image_url": img("cabin1"),
         "attributes": {"bedrooms": 3, "sleeps": 6, "min_nights": 2, "amenities": "WiFi, Kitchen, Dock", "available": "May-October"}},
        {"title": "Cozy in-town guesthouse", "price": 95, "city": "Ames, IA", "phone": "515-555-1002",
         "description": "Walk to ISU football games. Great for parents.",
         "image_url": img("guest1"),
         "attributes": {"bedrooms": 1, "sleeps": 2, "min_nights": 1, "amenities": "WiFi, Coffee maker, Parking", "available": "Year-round"}},
        {"title": "Family farmhouse rental", "price": 220, "city": "Ames, IA", "phone": "515-555-1003",
         "description": "Restored 1920s farmhouse on 5 acres.",
         "image_url": img("farm1"),
         "attributes": {"bedrooms": 4, "sleeps": 8, "min_nights": 2, "amenities": "WiFi, Full kitchen, Fire pit", "available": "April-November"}},
    ],

    # ---------- Services ----------
    "computer-tech": [
        {"title": "Computer repair and tune-up", "price": 60, "city": "Ames, IA", "phone": "515-555-1101",
         "description": "Hardware diagnostics, virus removal, OS reinstall.",
         "image_url": img("tech1"),
         "attributes": {"service_type": "PC repair", "experience": 8, "rate": 60, "remote": "No", "availability": "Evenings, weekends"}},
        {"title": "Web development for small businesses", "price": 75, "city": "Ames, IA", "phone": "515-555-1102",
         "description": "Static sites, WordPress, e-commerce setup.",
         "image_url": img("tech2"),
         "attributes": {"service_type": "Web development", "experience": 5, "rate": 75, "remote": "Yes", "availability": "Flexible"}},
        {"title": "Home network and Wi-Fi setup", "price": 50, "city": "Ames, IA", "phone": "515-555-1103",
         "description": "Mesh routers, smart-home device setup, troubleshooting.",
         "image_url": img("tech3"),
         "attributes": {"service_type": "Networking", "experience": 6, "rate": 50, "remote": "No", "availability": "Weekday evenings"}},
    ],
    "tutoring": [
        {"title": "Math tutor (algebra to calculus)", "price": 40, "city": "Ames, IA", "phone": "515-555-1201",
         "description": "Patient explainer, ISU math senior.",
         "image_url": img("tutor1"),
         "attributes": {"subject": "Mathematics", "level": "High School", "rate": 40, "experience": 3, "availability": "Mon-Thu evenings"}},
        {"title": "Spanish conversation tutor", "price": 35, "city": "Ames, IA", "phone": "515-555-1202",
         "description": "Native speaker, conversation-focused.",
         "image_url": img("tutor2"),
         "attributes": {"subject": "Spanish", "level": "Adult", "rate": 35, "experience": 5, "availability": "Tue/Thu/Sat"}},
        {"title": "SAT/ACT prep coaching", "price": 60, "city": "Ames, IA", "phone": "515-555-1203",
         "description": "Score-improvement focused. Practice tests included.",
         "image_url": img("tutor3"),
         "attributes": {"subject": "SAT/ACT prep", "level": "High School", "rate": 60, "experience": 7, "availability": "Weekends"}},
    ],
    "cleaning": [
        {"title": "Reliable house cleaning, weekly or biweekly", "price": 40, "city": "Ames, IA", "phone": "515-555-1301",
         "description": "Eco-friendly products, references on request.",
         "image_url": img("clean1"),
         "attributes": {"service_type": "Residential", "rate": 40, "supplies": "Yes", "experience": 6, "availability": "Weekdays"}},
        {"title": "Move-out deep clean", "price": 200, "city": "Ames, IA", "phone": "515-555-1302",
         "description": "Get your security deposit back. Flat rate per unit.",
         "image_url": img("clean2"),
         "attributes": {"service_type": "Move-in/Move-out", "rate": 200, "supplies": "Yes", "experience": 4, "availability": "On-call"}},
        {"title": "Office cleaning evenings", "price": 35, "city": "Ames, IA", "phone": "515-555-1303",
         "description": "Small offices, after-hours, insured.",
         "image_url": img("clean3"),
         "attributes": {"service_type": "Commercial", "rate": 35, "supplies": "Yes", "experience": 8, "availability": "Evenings"}},
    ],
    "moving": [
        {"title": "Two-person moving crew + truck", "price": 90, "city": "Ames, IA", "phone": "515-555-1401",
         "description": "Local moves, careful with fragile items.",
         "image_url": img("move1"),
         "attributes": {"service_type": "Local", "rate": 90, "truck": "Yes", "crew_size": 2, "availability": "Weekends"}},
        {"title": "Loading help only - $35/hr", "price": 35, "city": "Ames, IA", "phone": "515-555-1402",
         "description": "You provide truck, we provide muscle.",
         "image_url": img("move2"),
         "attributes": {"service_type": "Loading Help Only", "rate": 35, "truck": "No", "crew_size": 2, "availability": "Flexible"}},
        {"title": "Full-service apartment moves", "price": 110, "city": "Ames, IA", "phone": "515-555-1403",
         "description": "Pack, load, transport, unload. ISU-friendly rates.",
         "image_url": img("move3"),
         "attributes": {"service_type": "Full Service", "rate": 110, "truck": "Yes", "crew_size": 3, "availability": "Aug-Sept peak"}},
    ],
    "lawn-garden": [
        {"title": "Weekly lawn mowing", "price": 35, "city": "Ames, IA", "phone": "515-555-1501",
         "description": "Standard yards $35, larger yards quoted on site.",
         "image_url": img("lawn1"),
         "attributes": {"service_type": "Mowing", "rate": 35, "frequency": "Weekly", "experience": 4, "availability": "Apr-Oct"}},
        {"title": "Snow removal contracts", "price": 55, "city": "Ames, IA", "phone": "515-555-1502",
         "description": "Per-event or seasonal contracts.",
         "image_url": img("snow1"),
         "attributes": {"service_type": "Snow Removal", "rate": 55, "frequency": "Per event", "experience": 6, "availability": "Nov-Mar"}},
        {"title": "Landscape design & install", "price": 85, "city": "Ames, IA", "phone": "515-555-1503",
         "description": "Plant selection, mulching, paver patios.",
         "image_url": img("garden1"),
         "attributes": {"service_type": "Landscaping", "rate": 85, "frequency": "One-time", "experience": 10, "availability": "Spring/Summer"}},
    ],

    # ---------- Jobs ----------
    "software-engineering": [
        {"title": "Full-stack engineer (Python/React)", "price": 0, "city": "Ames, IA", "phone": "515-555-1601",
         "description": "Hybrid role at growing local SaaS company.",
         "image_url": img("job1"),
         "attributes": {"company": "Cyclone Software", "job_type": "Full-time", "experience": "3+ years", "salary": "$95k-$120k", "remote": "Hybrid"}},
        {"title": "Backend developer intern", "price": 0, "city": "Ames, IA", "phone": "515-555-1602",
         "description": "Summer 2026 internship. Java/Spring stack.",
         "image_url": img("job2"),
         "attributes": {"company": "Iowa Health Tech", "job_type": "Internship", "experience": "Junior or Senior", "salary": "$25/hr", "remote": "On-site"}},
        {"title": "DevOps engineer (remote OK)", "price": 0, "city": "Ames, IA", "phone": "515-555-1603",
         "description": "AWS, Terraform, Kubernetes. Iowa-based team.",
         "image_url": img("job3"),
         "attributes": {"company": "Prairie Cloud Inc.", "job_type": "Full-time", "experience": "5+ years", "salary": "$110k-$140k", "remote": "Remote"}},
    ],
    "customer-service": [
        {"title": "Call center representative", "price": 0, "city": "Ames, IA", "phone": "515-555-1701",
         "description": "Inbound calls for insurance company. Paid training.",
         "image_url": img("cs1"),
         "attributes": {"company": "Hawkeye Insurance", "job_type": "Full-time", "shift": "Day", "wage": 18.5, "experience": "Entry-level"}},
        {"title": "Front-desk receptionist", "price": 0, "city": "Ames, IA", "phone": "515-555-1702",
         "description": "Local clinic seeks friendly receptionist.",
         "image_url": img("cs2"),
         "attributes": {"company": "Ames Family Clinic", "job_type": "Part-time", "shift": "Day", "wage": 16.0, "experience": "1+ year preferred"}},
        {"title": "Email support specialist", "price": 0, "city": "Ames, IA", "phone": "515-555-1703",
         "description": "Help customers via email and chat for SaaS product.",
         "image_url": img("cs3"),
         "attributes": {"company": "Cyclone Software", "job_type": "Full-time", "shift": "Flexible", "wage": 21.0, "experience": "Customer service experience"}},
    ],
    "food-hospitality": [
        {"title": "Line cook - downtown bistro", "price": 0, "city": "Ames, IA", "phone": "515-555-1801",
         "description": "Busy farm-to-table restaurant. Evenings.",
         "image_url": img("food1"),
         "attributes": {"company": "Main Street Bistro", "job_type": "Full-time", "shift": "Evening", "wage": 17.0, "tips": "Yes"}},
        {"title": "Server - lunch shifts", "price": 0, "city": "Ames, IA", "phone": "515-555-1802",
         "description": "Tips average $25/hr. ISU students welcome.",
         "image_url": img("food2"),
         "attributes": {"company": "Cyclone Cafe", "job_type": "Part-time", "shift": "Morning", "wage": 9.0, "tips": "Yes"}},
        {"title": "Hotel front-desk overnight", "price": 0, "city": "Ames, IA", "phone": "515-555-1803",
         "description": "11pm-7am desk shift. Quiet most of the night.",
         "image_url": img("food3"),
         "attributes": {"company": "Iowa State Inn", "job_type": "Part-time", "shift": "Late Night", "wage": 16.0, "tips": "No"}},
    ],
    "education": [
        {"title": "Substitute teacher (K-12)", "price": 0, "city": "Ames, IA", "phone": "515-555-1901",
         "description": "Daily assignments throughout the school district.",
         "image_url": img("edu1"),
         "attributes": {"school": "Ames Community Schools", "job_type": "Substitute", "subject": "All grades", "salary": "$140/day", "certification": "Sub authorization required"}},
        {"title": "Math teacher - high school", "price": 0, "city": "Ames, IA", "phone": "515-555-1902",
         "description": "Algebra II and Pre-Calculus. Aug 2026 start.",
         "image_url": img("edu2"),
         "attributes": {"school": "Ames High School", "job_type": "Full-time", "subject": "Math (9-12)", "salary": "$48k-$62k", "certification": "Iowa teaching license"}},
        {"title": "After-school program leader", "price": 0, "city": "Ames, IA", "phone": "515-555-1903",
         "description": "Lead enrichment activities for grades 1-5.",
         "image_url": img("edu3"),
         "attributes": {"school": "Boys & Girls Club", "job_type": "Part-time", "subject": "Elementary enrichment", "salary": "$15/hr", "certification": "Background check"}},
    ],
    "retail": [
        {"title": "Sales associate - bookstore", "price": 0, "city": "Ames, IA", "phone": "515-555-2001",
         "description": "Friendly atmosphere, employee book discount.",
         "image_url": img("ret1"),
         "attributes": {"company": "Ames Reads", "job_type": "Part-time", "shift": "Flexible", "wage": 15.0, "experience": "None required"}},
        {"title": "Stocker - grocery store overnight", "price": 0, "city": "Ames, IA", "phone": "515-555-2002",
         "description": "10pm-6am stocking shelves. Shift differential pay.",
         "image_url": img("ret2"),
         "attributes": {"company": "Hy-Vee", "job_type": "Full-time", "shift": "Evening", "wage": 18.0, "experience": "None required"}},
        {"title": "Holiday seasonal cashiers", "price": 0, "city": "Ames, IA", "phone": "515-555-2003",
         "description": "Nov-Jan seasonal positions, possible permanent transition.",
         "image_url": img("ret3"),
         "attributes": {"company": "Target", "job_type": "Seasonal", "shift": "Weekend", "wage": 16.5, "experience": "None required"}},
    ],

    # ---------- Community ----------
    "events": [
        {"title": "Ames Farmers Market opening day", "price": 0, "city": "Ames, IA", "phone": "515-555-2101",
         "description": "Local produce, baked goods, live music.",
         "image_url": img("event1"),
         "attributes": {"event_date": "May 2, 2026", "event_time": "8:00 AM", "venue": "Downtown Ames", "event_type": "Festival", "free": "Yes"}},
        {"title": "ISU Cyclones home football", "price": 45, "city": "Ames, IA", "phone": "515-555-2102",
         "description": "Big 12 conference matchup. Tickets going fast.",
         "image_url": img("event2"),
         "attributes": {"event_date": "Sep 12, 2026", "event_time": "2:30 PM", "venue": "Jack Trice Stadium", "event_type": "Sports", "free": "No"}},
        {"title": "Free coding workshop for teens", "price": 0, "city": "Ames, IA", "phone": "515-555-2103",
         "description": "Intro to Python. Laptops provided.",
         "image_url": img("event3"),
         "attributes": {"event_date": "June 8, 2026", "event_time": "10:00 AM", "venue": "Ames Public Library", "event_type": "Workshop", "free": "Yes"}},
    ],
    "lost-found": [
        {"title": "Lost: Black Labrador near Brookside Park", "price": 0, "city": "Ames, IA", "phone": "515-555-2201",
         "description": "Friendly dog, answers to 'Buddy'. Reward offered.",
         "image_url": img("lost1"),
         "attributes": {"status": "Lost", "item": "Black Labrador (Buddy)", "color": "Black", "location": "Brookside Park", "date": "Apr 25, 2026"}},
        {"title": "Found: Set of keys at Memorial Union", "price": 0, "city": "Ames, IA", "phone": "515-555-2202",
         "description": "Found near the south entrance. Has a red lanyard.",
         "image_url": img("found1"),
         "attributes": {"status": "Found", "item": "Keys w/ red lanyard", "color": "Silver/Red", "location": "ISU Memorial Union", "date": "Apr 22, 2026"}},
        {"title": "Lost: Black wallet with student ID", "price": 0, "city": "Ames, IA", "phone": "515-555-2203",
         "description": "Lost on CyRide. ISU ID and credit cards inside.",
         "image_url": img("lost2"),
         "attributes": {"status": "Lost", "item": "Black bifold wallet", "color": "Black", "location": "CyRide Red Route", "date": "Apr 20, 2026"}},
    ],
    "volunteers": [
        {"title": "Food bank volunteers needed", "price": 0, "city": "Ames, IA", "phone": "515-555-2301",
         "description": "Help sort and pack donations Saturday mornings.",
         "image_url": img("vol1"),
         "attributes": {"organization": "MICA Food Pantry", "cause": "Food security", "commitment": "3 hrs/Saturday", "skills": "None required", "ongoing": "Yes"}},
        {"title": "Habitat for Humanity build day", "price": 0, "city": "Ames, IA", "phone": "515-555-2302",
         "description": "One-day build event. No experience needed.",
         "image_url": img("vol2"),
         "attributes": {"organization": "Habitat for Humanity", "cause": "Affordable housing", "commitment": "One Saturday", "skills": "Willing to learn", "ongoing": "No"}},
        {"title": "Tutor adult learners weekly", "price": 0, "city": "Ames, IA", "phone": "515-555-2303",
         "description": "Help adults work toward GED. Training provided.",
         "image_url": img("vol3"),
         "attributes": {"organization": "Ames Adult Literacy", "cause": "Education", "commitment": "2 hrs/week", "skills": "Patience, basic teaching", "ongoing": "Yes"}},
    ],
    "activities": [
        {"title": "Pickup soccer at Brookside", "price": 0, "city": "Ames, IA", "phone": "515-555-2401",
         "description": "Casual co-ed soccer, all skill levels welcome.",
         "image_url": img("act1"),
         "attributes": {"activity_type": "Soccer", "skill_level": "All Levels", "meeting_day": "Sundays", "meeting_time": "4:00 PM", "cost": "Free"}},
        {"title": "Board game nights", "price": 0, "city": "Ames, IA", "phone": "515-555-2402",
         "description": "Strategy and party games. Bring snacks to share.",
         "image_url": img("act2"),
         "attributes": {"activity_type": "Board games", "skill_level": "All Levels", "meeting_day": "Fridays", "meeting_time": "7:00 PM", "cost": "Free"}},
        {"title": "Yoga in the park", "price": 5, "city": "Ames, IA", "phone": "515-555-2403",
         "description": "Vinyasa flow class. Bring your own mat.",
         "image_url": img("act3"),
         "attributes": {"activity_type": "Yoga", "skill_level": "Beginner", "meeting_day": "Saturdays", "meeting_time": "9:00 AM", "cost": "$5 donation"}},
    ],
    "rideshare": [
        {"title": "Ames -> Des Moines daily commute", "price": 8, "city": "Ames, IA", "phone": "515-555-2501",
         "description": "Round-trip, share gas. Leaves 7am, returns 5:30pm.",
         "image_url": img("ride1"),
         "attributes": {"from_city": "Ames, IA", "to_city": "Des Moines, IA", "depart_date": "Mon-Fri", "depart_time": "7:00 AM", "seats": 2}},
        {"title": "Ames -> Chicago for Memorial Day", "price": 40, "city": "Ames, IA", "phone": "515-555-2502",
         "description": "One-way ride to downtown Chicago. Split tolls and gas.",
         "image_url": img("ride2"),
         "attributes": {"from_city": "Ames, IA", "to_city": "Chicago, IL", "depart_date": "May 22, 2026", "depart_time": "3:00 PM", "seats": 3}},
        {"title": "Ames -> Minneapolis weekly", "price": 25, "city": "Ames, IA", "phone": "515-555-2503",
         "description": "Heading home most weekends. Pickup near campus.",
         "image_url": img("ride3"),
         "attributes": {"from_city": "Ames, IA", "to_city": "Minneapolis, MN", "depart_date": "Most Fridays", "depart_time": "5:00 PM", "seats": 2}},
    ],
}


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------

def upsert_section(slug: str, name: str) -> int:
    db.execute(
        "INSERT INTO sections (slug, name) VALUES (%s, %s) "
        "ON DUPLICATE KEY UPDATE name = VALUES(name)",
        (slug, name),
    )
    return db.query_one("SELECT id FROM sections WHERE slug = %s", (slug,))["id"]


def upsert_category(section_id: int, slug: str, name: str) -> int:
    db.execute(
        "INSERT INTO categories (section_id, slug, name) VALUES (%s, %s, %s) "
        "ON DUPLICATE KEY UPDATE name = VALUES(name), section_id = VALUES(section_id)",
        (section_id, slug, name),
    )
    return db.query_one("SELECT id FROM categories WHERE slug = %s", (slug,))["id"]


def upsert_demo_user(username: str, password: str) -> int:
    existing = db.query_one("SELECT id FROM users WHERE username = %s", (username,))
    if existing:
        return existing["id"]
    hashed = bcrypt.generate_password_hash(password).decode("utf-8")
    return db.execute(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
        (username, hashed),
    )


def main():
    print("Seeding sections + categories...")
    section_ids = {s["slug"]: upsert_section(s["slug"], s["name"]) for s in SECTIONS}

    category_ids = {}
    for slug, cat in CATEGORIES.items():
        category_ids[slug] = upsert_category(section_ids[cat["section"]], slug, cat["name"])

    print("Seeding demo user (admin / Password55)...")
    demo_user_id = upsert_demo_user("admin", "Password55")

    print("Seeding listings...")
    inserted = 0
    for cat_slug, items in LISTINGS.items():
        existing = db.query_one(
            "SELECT COUNT(*) AS n FROM listings WHERE category_id = %s",
            (category_ids[cat_slug],),
        )["n"]
        if existing >= 3:
            print(f"  {cat_slug}: already has {existing} listings, skipping")
            continue
        for item in items:
            db.execute(
                """
                INSERT INTO listings
                  (category_id, user_id, title, price, city, phone,
                   description, image_url, attributes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    category_ids[cat_slug],
                    demo_user_id,
                    item["title"],
                    item["price"],
                    item["city"],
                    item["phone"],
                    item["description"],
                    item["image_url"],
                    json.dumps(item["attributes"]),
                ),
            )
            inserted += 1
        print(f"  {cat_slug}: +{len(items)} listings")

    print(f"\nDone. Inserted {inserted} new listings.")
    print("Login as 'admin' / 'Password55' to post new listings.")


if __name__ == "__main__":
    main()
