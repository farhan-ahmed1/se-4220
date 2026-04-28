"""
Section / category catalog and per-category attribute schemas.

Every listing has a fixed set of common columns (title, price, city, phone,
description, image_url) plus 4-5 category-specific attributes stored in the
listings.attributes JSON column. That keeps the assignment's "8-10 attributes
per item" requirement without needing 25 separate tables.

This file is the single source of truth used by:
  - seed.py        to populate sections + categories
  - app.py         to render the new-listing form and validate submissions
  - templates/*    to render attribute labels on listing detail pages
"""

# Field types understood by the form template:
#   text   - <input type="text">
#   number - <input type="number">
#   select - <select> with `options`

SECTIONS = [
    {"slug": "for-sale",  "name": "For Sale"},
    {"slug": "housing",   "name": "Housing"},
    {"slug": "services",  "name": "Services"},
    {"slug": "jobs",      "name": "Jobs"},
    {"slug": "community", "name": "Community"},
]

CONDITIONS = ["New", "Like New", "Good", "Fair", "Poor"]

CATEGORIES = {
    # ---------- For Sale ----------
    "cars-trucks": {
        "section": "for-sale", "name": "Cars + Trucks",
        "attributes": [
            {"key": "year",      "label": "Year",       "type": "number"},
            {"key": "make_model","label": "Make/Model", "type": "text"},
            {"key": "color",     "label": "Color",      "type": "text"},
            {"key": "mileage",   "label": "Mileage",    "type": "number"},
            {"key": "condition", "label": "Condition",  "type": "select", "options": CONDITIONS},
        ],
    },
    "motorcycles": {
        "section": "for-sale", "name": "Motorcycles",
        "attributes": [
            {"key": "year",       "label": "Year",       "type": "number"},
            {"key": "make_model", "label": "Make/Model", "type": "text"},
            {"key": "color",      "label": "Color",      "type": "text"},
            {"key": "mileage",    "label": "Mileage",    "type": "number"},
            {"key": "condition",  "label": "Condition",  "type": "select", "options": CONDITIONS},
        ],
    },
    "boats": {
        "section": "for-sale", "name": "Boats",
        "attributes": [
            {"key": "year_built", "label": "Year Built", "type": "number"},
            {"key": "make_model", "label": "Make/Model", "type": "text"},
            {"key": "color",      "label": "Color",      "type": "text"},
            {"key": "boat_type",  "label": "Type",       "type": "text"},
            {"key": "condition",  "label": "Condition",  "type": "select", "options": CONDITIONS},
        ],
    },
    "books": {
        "section": "for-sale", "name": "Books",
        "attributes": [
            {"key": "title_book", "label": "Book Title", "type": "text"},
            {"key": "author",     "label": "Author",     "type": "text"},
            {"key": "genre",      "label": "Genre",      "type": "text"},
            {"key": "format",     "label": "Format",     "type": "select",
             "options": ["Hardcover", "Paperback", "eBook"]},
            {"key": "condition",  "label": "Condition",  "type": "select", "options": CONDITIONS},
        ],
    },
    "furniture": {
        "section": "for-sale", "name": "Furniture",
        "attributes": [
            {"key": "item_type", "label": "Type",      "type": "text"},
            {"key": "material",  "label": "Material",  "type": "text"},
            {"key": "color",     "label": "Color",     "type": "text"},
            {"key": "dimensions","label": "Dimensions","type": "text"},
            {"key": "condition", "label": "Condition", "type": "select", "options": CONDITIONS},
        ],
    },

    # ---------- Housing ----------
    "apartments-rent": {
        "section": "housing", "name": "Apartments for Rent",
        "attributes": [
            {"key": "bedrooms",  "label": "Bedrooms",  "type": "number"},
            {"key": "bathrooms", "label": "Bathrooms", "type": "number"},
            {"key": "sqft",      "label": "Square Feet", "type": "number"},
            {"key": "pets",      "label": "Pets Allowed", "type": "select",
             "options": ["Yes", "No", "Cats only", "Dogs only"]},
            {"key": "available", "label": "Available From", "type": "text"},
        ],
    },
    "houses-sale": {
        "section": "housing", "name": "Houses for Sale",
        "attributes": [
            {"key": "bedrooms",   "label": "Bedrooms",  "type": "number"},
            {"key": "bathrooms",  "label": "Bathrooms", "type": "number"},
            {"key": "sqft",       "label": "Square Feet", "type": "number"},
            {"key": "lot_size",   "label": "Lot Size", "type": "text"},
            {"key": "year_built", "label": "Year Built", "type": "number"},
        ],
    },
    "rooms-roommates": {
        "section": "housing", "name": "Rooms / Roommates",
        "attributes": [
            {"key": "rent",      "label": "Monthly Rent", "type": "number"},
            {"key": "furnished", "label": "Furnished", "type": "select", "options": ["Yes", "No"]},
            {"key": "private_bath", "label": "Private Bath", "type": "select", "options": ["Yes", "No"]},
            {"key": "available", "label": "Available From", "type": "text"},
            {"key": "lease",     "label": "Lease Length", "type": "text"},
        ],
    },
    "sublets": {
        "section": "housing", "name": "Sublets",
        "attributes": [
            {"key": "bedrooms",  "label": "Bedrooms",  "type": "number"},
            {"key": "start_date","label": "Start Date","type": "text"},
            {"key": "end_date",  "label": "End Date",  "type": "text"},
            {"key": "furnished", "label": "Furnished", "type": "select", "options": ["Yes", "No"]},
            {"key": "utilities", "label": "Utilities Included", "type": "select", "options": ["Yes", "No", "Some"]},
        ],
    },
    "vacation-rentals": {
        "section": "housing", "name": "Vacation Rentals",
        "attributes": [
            {"key": "bedrooms",   "label": "Bedrooms", "type": "number"},
            {"key": "sleeps",     "label": "Sleeps",   "type": "number"},
            {"key": "min_nights", "label": "Min Nights", "type": "number"},
            {"key": "amenities",  "label": "Amenities", "type": "text"},
            {"key": "available",  "label": "Available Dates", "type": "text"},
        ],
    },

    # ---------- Services ----------
    "computer-tech": {
        "section": "services", "name": "Computer / Tech",
        "attributes": [
            {"key": "service_type", "label": "Service Type", "type": "text"},
            {"key": "experience",   "label": "Years Experience", "type": "number"},
            {"key": "rate",         "label": "Rate (USD/hr)", "type": "number"},
            {"key": "remote",       "label": "Remote Available", "type": "select", "options": ["Yes", "No"]},
            {"key": "availability", "label": "Availability", "type": "text"},
        ],
    },
    "tutoring": {
        "section": "services", "name": "Tutoring",
        "attributes": [
            {"key": "subject",     "label": "Subject", "type": "text"},
            {"key": "level",       "label": "Level",   "type": "select",
             "options": ["Elementary", "Middle School", "High School", "College", "Adult"]},
            {"key": "rate",        "label": "Rate (USD/hr)", "type": "number"},
            {"key": "experience",  "label": "Years Experience", "type": "number"},
            {"key": "availability","label": "Availability", "type": "text"},
        ],
    },
    "cleaning": {
        "section": "services", "name": "Cleaning",
        "attributes": [
            {"key": "service_type", "label": "Service Type", "type": "select",
             "options": ["Residential", "Commercial", "Move-in/Move-out", "Deep Clean"]},
            {"key": "rate",         "label": "Rate (USD/hr)", "type": "number"},
            {"key": "supplies",     "label": "Supplies Provided", "type": "select", "options": ["Yes", "No"]},
            {"key": "experience",   "label": "Years Experience", "type": "number"},
            {"key": "availability", "label": "Availability", "type": "text"},
        ],
    },
    "moving": {
        "section": "services", "name": "Moving",
        "attributes": [
            {"key": "service_type", "label": "Service Type", "type": "select",
             "options": ["Local", "Long Distance", "Loading Help Only", "Full Service"]},
            {"key": "rate",         "label": "Rate (USD/hr)", "type": "number"},
            {"key": "truck",        "label": "Truck Provided", "type": "select", "options": ["Yes", "No"]},
            {"key": "crew_size",    "label": "Crew Size", "type": "number"},
            {"key": "availability", "label": "Availability", "type": "text"},
        ],
    },
    "lawn-garden": {
        "section": "services", "name": "Lawn / Garden",
        "attributes": [
            {"key": "service_type", "label": "Service Type", "type": "select",
             "options": ["Mowing", "Landscaping", "Snow Removal", "Tree Service", "Full Yard Care"]},
            {"key": "rate",         "label": "Rate (USD/visit)", "type": "number"},
            {"key": "frequency",    "label": "Frequency", "type": "text"},
            {"key": "experience",   "label": "Years Experience", "type": "number"},
            {"key": "availability", "label": "Availability", "type": "text"},
        ],
    },

    # ---------- Jobs ----------
    "software-engineering": {
        "section": "jobs", "name": "Software / Engineering",
        "attributes": [
            {"key": "company",     "label": "Company", "type": "text"},
            {"key": "job_type",    "label": "Job Type", "type": "select",
             "options": ["Full-time", "Part-time", "Contract", "Internship"]},
            {"key": "experience",  "label": "Required Experience", "type": "text"},
            {"key": "salary",      "label": "Salary Range", "type": "text"},
            {"key": "remote",      "label": "Remote", "type": "select",
             "options": ["On-site", "Hybrid", "Remote"]},
        ],
    },
    "customer-service": {
        "section": "jobs", "name": "Customer Service",
        "attributes": [
            {"key": "company",     "label": "Company", "type": "text"},
            {"key": "job_type",    "label": "Job Type", "type": "select",
             "options": ["Full-time", "Part-time", "Contract"]},
            {"key": "shift",       "label": "Shift", "type": "select",
             "options": ["Day", "Evening", "Night", "Flexible"]},
            {"key": "wage",        "label": "Wage (USD/hr)", "type": "number"},
            {"key": "experience",  "label": "Required Experience", "type": "text"},
        ],
    },
    "food-hospitality": {
        "section": "jobs", "name": "Food / Hospitality",
        "attributes": [
            {"key": "company",  "label": "Restaurant / Hotel", "type": "text"},
            {"key": "job_type", "label": "Job Type", "type": "select",
             "options": ["Full-time", "Part-time", "Seasonal"]},
            {"key": "shift",    "label": "Shift", "type": "select",
             "options": ["Morning", "Afternoon", "Evening", "Late Night"]},
            {"key": "wage",     "label": "Wage (USD/hr)", "type": "number"},
            {"key": "tips",     "label": "Tips", "type": "select", "options": ["Yes", "No"]},
        ],
    },
    "education": {
        "section": "jobs", "name": "Education",
        "attributes": [
            {"key": "school",     "label": "School / Institution", "type": "text"},
            {"key": "job_type",   "label": "Job Type", "type": "select",
             "options": ["Full-time", "Part-time", "Substitute", "Contract"]},
            {"key": "subject",    "label": "Subject / Grade", "type": "text"},
            {"key": "salary",     "label": "Salary Range", "type": "text"},
            {"key": "certification", "label": "Certification Required", "type": "text"},
        ],
    },
    "retail": {
        "section": "jobs", "name": "Retail",
        "attributes": [
            {"key": "company",  "label": "Store", "type": "text"},
            {"key": "job_type", "label": "Job Type", "type": "select",
             "options": ["Full-time", "Part-time", "Seasonal"]},
            {"key": "shift",    "label": "Shift", "type": "select",
             "options": ["Day", "Evening", "Weekend", "Flexible"]},
            {"key": "wage",     "label": "Wage (USD/hr)", "type": "number"},
            {"key": "experience","label": "Required Experience", "type": "text"},
        ],
    },

    # ---------- Community ----------
    "events": {
        "section": "community", "name": "Events",
        "attributes": [
            {"key": "event_date", "label": "Event Date", "type": "text"},
            {"key": "event_time", "label": "Event Time", "type": "text"},
            {"key": "venue",      "label": "Venue",      "type": "text"},
            {"key": "event_type", "label": "Event Type", "type": "select",
             "options": ["Music", "Sports", "Festival", "Workshop", "Charity", "Other"]},
            {"key": "free",       "label": "Free Admission", "type": "select", "options": ["Yes", "No"]},
        ],
    },
    "lost-found": {
        "section": "community", "name": "Lost + Found",
        "attributes": [
            {"key": "status",   "label": "Status", "type": "select", "options": ["Lost", "Found"]},
            {"key": "item",     "label": "Item",   "type": "text"},
            {"key": "color",    "label": "Color",  "type": "text"},
            {"key": "location", "label": "Location", "type": "text"},
            {"key": "date",     "label": "Date",     "type": "text"},
        ],
    },
    "volunteers": {
        "section": "community", "name": "Volunteers",
        "attributes": [
            {"key": "organization", "label": "Organization", "type": "text"},
            {"key": "cause",        "label": "Cause", "type": "text"},
            {"key": "commitment",   "label": "Time Commitment", "type": "text"},
            {"key": "skills",       "label": "Skills Needed", "type": "text"},
            {"key": "ongoing",      "label": "Ongoing", "type": "select", "options": ["Yes", "No"]},
        ],
    },
    "activities": {
        "section": "community", "name": "Activities",
        "attributes": [
            {"key": "activity_type", "label": "Activity Type", "type": "text"},
            {"key": "skill_level",   "label": "Skill Level", "type": "select",
             "options": ["Beginner", "Intermediate", "Advanced", "All Levels"]},
            {"key": "meeting_day",   "label": "Meeting Day", "type": "text"},
            {"key": "meeting_time",  "label": "Meeting Time", "type": "text"},
            {"key": "cost",          "label": "Cost", "type": "text"},
        ],
    },
    "rideshare": {
        "section": "community", "name": "Rideshare",
        "attributes": [
            {"key": "from_city",  "label": "From", "type": "text"},
            {"key": "to_city",    "label": "To",   "type": "text"},
            {"key": "depart_date","label": "Departure Date", "type": "text"},
            {"key": "depart_time","label": "Departure Time", "type": "text"},
            {"key": "seats",      "label": "Seats Available", "type": "number"},
        ],
    },
}


def categories_for_section(section_slug):
    """Return list of (slug, dict) for categories within a given section, in
    the order they appear in CATEGORIES."""
    return [
        (slug, cat)
        for slug, cat in CATEGORIES.items()
        if cat["section"] == section_slug
    ]
