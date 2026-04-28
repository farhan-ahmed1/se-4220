# Creating a Cloud-Based Advertisement Website

Create a cloud-based classified ads website with the following sections:

1. For Sale
2. Housing
3. Services
4. Jobs
5. Community

Each section will have five categories (or more.) For example, under "For Sale" section you could have the
following 5 categories:

**For Sale:**

a. Cars + Trucks
b. Motorcycles
c. Boats
d. Books
e. Furniture

Each category will have at least 3 items stored in a structured table with 8-10 attributes.
For example, each Boat item will have the following attributes:

1. Year Built
2. Make/Model
3. Color
4. Type
5. Condition
6. Price
7. Description
8. Price
9. City
10. Phone number

You will build ONE city website to cover one geographical area Ames, Iowa.

Your project will include building the web application and deploying it on the GCP cloud. The
website will have two major user roles:

- **Visitor**, with access to all data items under all categories in a read-only mode, no logon required.
- **Registered users**, with the ability to create a new item entry under one of the supported
  categories. The new listing must have all fields of the entry filled completed before it is published
  on the website.

You have the freedom to choose your cloud architecture including the type of database
and other cloud tools and frameworks.

## Initial Data Population

- The cloud application will allow non-registered users to view all contents.
- The cloud application will allow users to create an account (register)

Only registered users can create a new listing. The data should be
validated before it is accepted and uploaded to the database and becomes
listed.

## Initial Data Size

Your website will have existing data by the time of your final project delivery with the following minimum:

- 5 sections with 5 categories per section (a total of 25 categories or more)
- Each category will have at least 3 items (for example 3 cars and 3 boats, etc.)

You can create the initial data manually or use any script or tool to automate populating your database.

Please also create diagrams of system architecture and a technical report of the technologies used and how it works in markdown.

## Clarifications

This is a class demo. Therefore it should be as simple as possible. You don't need to worry about security,
heavy validation of user input, scalability, robust authentication, location features or advanced UI.
Pick well-known and simple technologies. Please write all the necessary files in this directory Project-5.
